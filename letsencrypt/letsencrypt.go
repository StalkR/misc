/*
Binary letsencrypt manages Let's Encrypt certificates.

Given:
- a list of domains
- a directory where to put the http-01 acme challenges for those domains
- a directory where to save the certificates and keys

It handles everything from creation to update before it expires.
Call it with cron regularly (e.g. weekly) and you are all set.

A temporary account key is created as needed and not saved.
*/
package main

import (
	"context"
	"crypto/rand"
	"crypto/rsa"
	"crypto/x509"
	"crypto/x509/pkix"
	"encoding/pem"
	"flag"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/crypto/acme"
)

var (
	domains = flag.String("domains", "", "List of domains to manage.")
	certDir = flag.String("cert_dir", "", "Certificates and keys directory.")
	acmeDir = flag.String("acme_dir", "", "ACME challenge directory.")
)

// updateBefore is the delay to update certificates before expiration.
const updateBefore = 30 * 24 * time.Hour // 30 days

func main() {
	flag.Parse()
	if *domains == "" || *certDir == "" || *acmeDir == "" {
		flag.Usage()
		os.Exit(1)
	}
	ctx := context.Background()

	for _, domain := range strings.Split(*domains, ",") {
		if err := manage(ctx, domain); err != nil {
			log.Fatal(err)
		}
	}
}

// manage creates and updates certificates for a domain as needed.
func manage(ctx context.Context, domain string) error {
	certFile := filepath.Join(*certDir, domain+".crt")
	certPEM, err := ioutil.ReadFile(certFile)
	if err != nil {
		if os.IsNotExist(err) {
			log.Printf("[+] %v: no cert, creating", domain)
			return create(ctx, domain)
		}
		return fmt.Errorf("could not read cert for %v: %v", domain, err)
	}
	certs, err := parseCertificates(certPEM)
	if err != nil {
		return err
	}
	var cert *x509.Certificate
	for _, e := range certs {
		if e.Subject.CommonName == domain {
			cert = e
		}
	}
	if cert == nil {
		return fmt.Errorf("cert for %v not found in chain", domain)
	}
	if time.Now().Add(updateBefore).Before(cert.NotAfter) {
		log.Printf("[*] %v: expires %v, nothing to do", domain, cert.NotAfter)
		return nil
	}
	log.Printf("[+] %v: expires %v, updating", domain, cert.NotAfter)
	return create(ctx, domain)
}

// parseCertificates parses PEM certificates.
func parseCertificates(certPEM []byte) ([]*x509.Certificate, error) {
	var certificates []*x509.Certificate
	for {
		block, rest := pem.Decode(certPEM)
		if block == nil {
			return nil, fmt.Errorf("failed to parse certificate PEM")
		}
		cert, err := x509.ParseCertificate(block.Bytes)
		if err != nil {
			return nil, fmt.Errorf("failed to parse certificate: %v", err)
		}
		certificates = append(certificates, cert)
		if len(rest) == 0 {
			break
		}
		certPEM = rest
	}
	return certificates, nil
}

// create obtains a certificate and saves it on disk with the key.
func create(ctx context.Context, domain string) error {
	cert, key, err := obtainCert(ctx, domain)
	if err != nil {
		return fmt.Errorf("obtain cert for %v: %v", domain, err)
	}
	certFile := filepath.Join(*certDir, domain+".crt")
	if err := ioutil.WriteFile(certFile, []byte(cert), 0644); err != nil {
		return err
	}
	keyFile := filepath.Join(*certDir, domain+".key")
	if err := ioutil.WriteFile(keyFile, []byte(key), 0640); err != nil {
		return err
	}
	return nil
}

// obtainCert creates a key and obtains a signed certificate.
// It returns the signed certificate with chain and the key, both PEM encoded.
// A temporary account key is created and not saved.
func obtainCert(ctx context.Context, domain string) (cert, key string, err error) {
	certKey, err := rsa.GenerateKey(rand.Reader, 4096)
	if err != nil {
		return "", "", fmt.Errorf("cert key: %v", err)
	}

	req := &x509.CertificateRequest{
		Subject: pkix.Name{CommonName: domain},
	}
	req.DNSNames = []string{domain}
	csr, err := x509.CreateCertificateRequest(rand.Reader, req, certKey)
	if err != nil {
		return "", "", fmt.Errorf("csr: %v", err)
	}

	accountKey, err := rsa.GenerateKey(rand.Reader, 2048)
	if err != nil {
		return "", "", fmt.Errorf("account key: %v", err)
	}
	client := &acme.Client{
		Key:          accountKey,
		DirectoryURL: acme.LetsEncryptURL,
	}
	if _, err = client.Register(ctx, &acme.Account{}, acme.AcceptTOS); err != nil {
		return "", "", fmt.Errorf("register: %v", err)
	}

	if err := authorize(ctx, client, domain); err != nil {
		return "", "", err
	}

	const expiry = 90 * 24 * time.Hour // 90 days, desired
	const bundle = true
	certDER, _, err := client.CreateCert(ctx, csr, expiry, bundle)
	if err != nil {
		return "", "", fmt.Errorf("create cert: %v", err)
	}

	var certPEM []byte
	for _, b := range certDER {
		b = pem.EncodeToMemory(&pem.Block{Type: "CERTIFICATE", Bytes: b})
		certPEM = append(certPEM, b...)
	}
	certKeyPEM := pem.EncodeToMemory(&pem.Block{Type: "RSA PRIVATE KEY",
		Bytes: x509.MarshalPKCS1PrivateKey(certKey)})

	return string(certPEM), string(certKeyPEM), nil
}

// authorize authorizes the client to issue certificates for this domain
// by going through the http-01 challenge.
func authorize(ctx context.Context, client *acme.Client, domain string) error {
	authorization, err := client.Authorize(ctx, domain)
	if err != nil {
		return fmt.Errorf("authorize: %v", err)
	}
	if authorization.Status == acme.StatusValid {
		return nil
	}

	var challenge *acme.Challenge
	for _, c := range authorization.Challenges {
		if c.Type == "http-01" {
			challenge = c
			break
		}
	}
	if challenge == nil {
		return fmt.Errorf("no http-01 challenge offered")
	}

	response, err := client.HTTP01ChallengeResponse(challenge.Token)
	if err != nil {
		return fmt.Errorf("challenge response: %v", err)
	}

	challengeFile := filepath.Join(*acmeDir, challenge.Token)
	if err := ioutil.WriteFile(challengeFile, []byte(response), 0644); err != nil {
		return fmt.Errorf("could not write challenge: %v", err)
	}
	defer os.Remove(challengeFile)

	if _, err := client.Accept(ctx, challenge); err != nil {
		return fmt.Errorf("accept challenge: %v", err)
	}
	if _, err = client.WaitAuthorization(ctx, authorization.URI); err != nil {
		return fmt.Errorf("authorization: %v", err)
	}
	return nil
}
