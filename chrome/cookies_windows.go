//go:build windows

package chrome

import (
  "bytes"
  "crypto/aes"
  "crypto/cipher"
  "database/sql"
  "encoding/base64"
  "encoding/json"
  "fmt"
  "os"
  "path/filepath"
  "syscall"
  "unsafe"

  // if you have a compile error due to linker and mingw,
  // make sure you're using TDM-GCC-64 not cygwin's
  // e.g. you can do PATH=/cygdrive/c/TDM-GCC-64/bin:$PATH go build .
  _ "github.com/mattn/go-sqlite3"
)

// Cookies returns Chrome cookies (name -> value) for a given host.
//
// Cookies are read from Chrome's SQLite database and decrypted with Windows DPAPI.
func Cookies(host string) (map[string]string, error) {
  localAppData, err := os.UserCacheDir()
  if err != nil {
    return nil, err
  }

  localStatePath := filepath.Join(localAppData, "Google", "Chrome", "User Data", "Local State")
  f, err := os.Open(localStatePath)
  if err != nil {
    return nil, err
  }
  defer f.Close()
  var v struct {
    OSCrypt struct {
      EncryptedKey string `json:"encrypted_key"`
    } `json:"os_crypt"`
  }
  if err := json.NewDecoder(f).Decode(&v); err != nil {
    return nil, err
  }
  encryptedKey, err := base64.StdEncoding.DecodeString(v.OSCrypt.EncryptedKey)
  if err != nil {
    return nil, err
  }
  const magic = "DPAPI"
  if got := encryptedKey[:5]; !bytes.Equal(got, []byte(magic)) {
    return nil, fmt.Errorf("got encrypted key magic %v, want %v", got, magic)
  }
  key, err := cryptUnprotectData(encryptedKey[len(magic):])
  if err != nil {
    return nil, err
  }

  dbPath := filepath.Join(localAppData, "Google", "Chrome", "User Data", "Default", "Network", "Cookies")
  db, err := sql.Open("sqlite3", dbPath)
  if err != nil {
    return nil, err
  }
  defer db.Close()

  stmt, err := db.Prepare("SELECT name, encrypted_value FROM cookies WHERE host_key = ?")
  if err != nil {
    return nil, err
  }
  defer stmt.Close()
  rows, err := stmt.Query(host)
  if err != nil {
    return nil, err
  }
  defer rows.Close()

  cookies := map[string]string{}
  for rows.Next() {
    var name string
    var encryptedValue []byte
    if err := rows.Scan(&name, &encryptedValue); err != nil {
      return nil, err
    }

    version := encryptedValue[:3]
    nonce := encryptedValue[3:][:12]
    ciphertext := encryptedValue[3+12:]
    if want := []byte("v10"); !bytes.Equal(version, want) {
      return nil, fmt.Errorf("got encrypted cookie (%v) version %v, want %v", name, string(version), string(want))
    }

    block, err := aes.NewCipher(key)
    if err != nil {
      return nil, err
    }
    aesgcm, err := cipher.NewGCM(block)
    if err != nil {
      return nil, err
    }
    plaintext, err := aesgcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {
      return nil, err
    }
    cookies[name] = string(plaintext)
  }
  return cookies, nil
}

var (
  dllcrypt32  = syscall.NewLazyDLL("Crypt32.dll")
  dllkernel32 = syscall.NewLazyDLL("Kernel32.dll")

  procEncryptData = dllcrypt32.NewProc("CryptProtectData")
  procDecryptData = dllcrypt32.NewProc("CryptUnprotectData")
  procLocalFree   = dllkernel32.NewProc("LocalFree")
)

type dataBlob struct {
  cbData uint32
  pbData *byte
}

func newBlob(d []byte) *dataBlob {
  if len(d) == 0 {
    return &dataBlob{}
  }
  return &dataBlob{
    cbData: uint32(len(d)),
    pbData: &d[0],
  }
}

func (b *dataBlob) bytes() []byte {
  d := make([]byte, b.cbData)
  copy(d, (*[1 << 30]byte)(unsafe.Pointer(b.pbData))[:])
  return d
}

// https://msdn.microsoft.com/en-us/library/windows/desktop/aa380882(v=vs.85).aspx
func cryptUnprotectData(data []byte) ([]byte, error) {
  var outblob dataBlob
  // [in]            DATA_BLOB                 *pDataIn,
  pDataIn := uintptr(unsafe.Pointer(newBlob(data)))
  // [out, optional] LPWSTR                    *ppszDataDescr,
  ppszDataDescr := uintptr(0)
  // [in, optional]  DATA_BLOB                 *pOptionalEntropy,
  pOptionalEntropy := uintptr(0)
  //              PVOID                     pvReserved,
  pvReserved := uintptr(0)
  // [in, optional]  CRYPTPROTECT_PROMPTSTRUCT *pPromptStruct,
  pPromptStruct := uintptr(0)
  // [in]            DWORD                     dwFlags,
  const CRYPTPROTECT_UI_FORBIDDEN = 0x1
  const CRYPTPROTECT_LOCAL_MACHINE = 0x4
  dwFlags := uintptr(CRYPTPROTECT_LOCAL_MACHINE)
  // [out]           DATA_BLOB                 *pDataOut
  pDataOut := uintptr(unsafe.Pointer(&outblob))
  r, _, err := procDecryptData.Call(pDataIn, ppszDataDescr, pOptionalEntropy, pvReserved, pPromptStruct, dwFlags, pDataOut)
  if r == 0 {
    return nil, err
  }
  defer procLocalFree.Call(uintptr(unsafe.Pointer(outblob.pbData)))
  return outblob.bytes(), nil
}
