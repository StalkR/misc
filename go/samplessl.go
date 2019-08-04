// Sample self-signed SSL service.
package main

import (
	"bufio"
	"crypto/rand"
	"crypto/rsa"
	"crypto/tls"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"flag"
	"fmt"
	"log"
	"math/big"
	"net"
	"time"
)

var flagPort = flag.Int("port", 1443, "Port to listen on.")

func main() {
	flag.Parse()
	if err := launch(); err != nil {
		log.Fatal(err)
	}
}

func launch() error {
	cert, err := createCert()
	if err != nil {
		return err
	}
	cfg := &tls.Config{Certificates: []tls.Certificate{cert}}
	ln, err := tls.Listen("tcp", fmt.Sprintf(":%v", *flagPort), cfg)
	if err != nil {
		return err
	}
	defer ln.Close()
	log.Printf("Ready to serve :%v", *flagPort)
	for {
		conn, err := ln.Accept()
		if err != nil {
			log.Printf("[%v] read: %v", conn.RemoteAddr(), err)
			continue
		}
		go handle(conn)
	}
}

func createCert() (tls.Certificate, error) {
	tmpl := &x509.Certificate{
		SerialNumber:          big.NewInt(1337),
		Subject:               pkix.Name{CommonName: "service"},
		NotBefore:             time.Now(),
		NotAfter:              time.Now().Add(time.Hour * 24 * 7), // 7 days
		IsCA:                  true,
		ExtKeyUsage:           []x509.ExtKeyUsage{x509.ExtKeyUsageServerAuth},
		KeyUsage:              x509.KeyUsageDigitalSignature | x509.KeyUsageCertSign,
		BasicConstraintsValid: true,
	}
	privateKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return tls.Certificate{}, err
	}
	parent := tmpl // self-signed certificate
	cert, err := x509.CreateCertificate(rand.Reader, tmpl, parent, &privateKey.PublicKey, privateKey)
	if err != nil {
		return tls.Certificate{}, err
	}
	certPem := pem.EncodeToMemory(&pem.Block{
		Type:  "CERTIFICATE",
		Bytes: cert})
	keyPem := pem.EncodeToMemory(&pem.Block{
		Type:  "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(privateKey)})
	return tls.X509KeyPair(certPem, keyPem)
}

func handle(conn net.Conn) {
	defer conn.Close()
	fmt.Fprintf(conn, "Question?\n")
	input, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		log.Printf("[%v] read: %v", conn.RemoteAddr(), err)
		return
	}
	input = input[:len(input)-1]
	fmt.Fprintf(conn, "Response: %v\n", input)
}
