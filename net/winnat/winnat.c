/*
winnat provides a very simple NAT for Windows using WinDirect.

Example use case:
 - you have servers listening on port 1234 and 5678
 - all clients connect to 1234
 - you want client 1.2.3.4 to be redirected to the one at 5678

Solution: winnat.exe src 1.2.3.4 proto tcp port 1234 to 5678

More flexibility and features left as an exercise to the reader.

Thanks to WindDirect https://github.com/basil00/Divert.
*/
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "windivert.h"

#define ntohs(x)            WinDivertHelperNtohs(x)
#define ntohl(x)            WinDivertHelperNtohl(x)
#define htons(x)            WinDivertHelperHtons(x)
#define htonl(x)            WinDivertHelperHtonl(x)

#define MAXBUF              WINDIVERT_MTU_MAX

int __cdecl main(int argc, char **argv) {
    char *src = NULL;
    UINT32 srcip = 0;
    char *proto_str;
    UINT8 proto = 0;
    UINT16 port = 0;
    UINT16 to = 0;
    INT16 priority = 0;
    for (int i = 1; i < argc; i += 2) {
        if (i+1 == argc) {
            fprintf(stderr, "[-] error: missing argument for \"%s\"\n", argv[i]);
            exit(EXIT_FAILURE);
        }
        if (!strcmp(argv[i], "src")) {
            src = argv[i+1];
            if (!WinDivertHelperParseIPv4Address(src, &srcip)) {
                fprintf(stderr, "[-] error: invalid src ip \"%s\"\n", src);
                exit(EXIT_FAILURE);
            }
            continue;
        }
        if (!strcmp(argv[i], "proto")) {
            proto_str = argv[i+1];
            if (!strcmp(proto_str, "tcp")) proto = IPPROTO_TCP;
            if (!strcmp(proto_str, "udp")) proto = IPPROTO_UDP;
            continue;
        }
        if (!strcmp(argv[i], "port")) {
            port = (UINT16)atoi(argv[i+1]);
            continue;
        }
        if (!strcmp(argv[i], "to")) {
            to = (UINT16)atoi(argv[i+1]);
            continue;
        }
        if (!strcmp(argv[i], "priority")) {
            priority = (INT16)atoi(argv[i+1]);
            continue;
        }
    }
    if (argc <= 1 || srcip == 0 || proto == 0 || port == 0 || to == 0) {
        fprintf(stderr, "usage: %s src 1.2.3.4 proto tcp|udp port 1234 to 5678 [priority 0]\n", argv[0]);
        exit(EXIT_FAILURE);
    }

    char filter[1024];
    if (sprintf_s(filter, sizeof(filter), "(inbound and ip.SrcAddr == %s and %s.DstPort == %i) or (outbound and ip.DstAddr == %s and %s.SrcPort == %i)", src, proto_str, port, src, proto_str, to) == -1) {
        fprintf(stderr, "[-] error: filter allocation failed\n");
        exit(EXIT_FAILURE);
    }
    HANDLE handle = WinDivertOpen(filter, WINDIVERT_LAYER_NETWORK, priority, 0);
    if (handle == INVALID_HANDLE_VALUE) {
        const char *err_str;
        if (GetLastError() == ERROR_INVALID_PARAMETER &&
            !WinDivertHelperCompileFilter(filter, WINDIVERT_LAYER_NETWORK, NULL, 0, &err_str, NULL)) {
            fprintf(stderr, "[-] error: invalid filter \"%s\"\n", err_str);
            exit(EXIT_FAILURE);
        }
        fprintf(stderr, "[-] error: failed to open the WinDivert device (%d)\n", GetLastError());
        exit(EXIT_FAILURE);
    }

    printf("[*] listening\n");
    while (TRUE) {
        unsigned char packet[MAXBUF];
        UINT packet_len;
        WINDIVERT_ADDRESS addr;
        if (!WinDivertRecv(handle, packet, sizeof(packet), &packet_len, &addr)) {
            fprintf(stderr, "[!] warning: failed to read packet\n");
            continue;
        }
       
        PWINDIVERT_IPHDR ip_header;
        PWINDIVERT_IPV6HDR ipv6_header;
        UINT8 protocol;
        PWINDIVERT_ICMPHDR icmp_header;
        PWINDIVERT_ICMPV6HDR icmpv6_header;
        PWINDIVERT_TCPHDR tcp_header;
        PWINDIVERT_UDPHDR udp_header;
        PVOID payload;
        UINT payload_len;
        WinDivertHelperParsePacket(packet, packet_len, &ip_header, &ipv6_header, &protocol, &icmp_header, &icmpv6_header, &tcp_header, &udp_header, &payload, &payload_len, NULL, NULL);
        if (ip_header == NULL) continue;

        char src_addr[16], dst_addr[16];
        WinDivertHelperFormatIPv4Address(ntohl(ip_header->SrcAddr), src_addr, sizeof(src_addr));
        WinDivertHelperFormatIPv4Address(ntohl(ip_header->DstAddr), dst_addr, sizeof(dst_addr));
        fprintf(stderr, "[*] packet (%i): %s src %s dst %s proto %s sport %i dport %i\n",
            packet_len,
            addr.Outbound ? "outbound" : "inbound",
            src_addr, dst_addr,
            protocol == IPPROTO_TCP ? "tcp" : "udp",
            protocol == IPPROTO_TCP ? ntohs(tcp_header->SrcPort) : ntohs(udp_header->SrcPort),
            protocol == IPPROTO_TCP ? ntohs(tcp_header->DstPort) : ntohs(udp_header->DstPort));

        if (!addr.Outbound) {
            switch (protocol) {
                case IPPROTO_TCP: tcp_header->DstPort = htons(to); break;
                case IPPROTO_UDP: udp_header->DstPort = htons(to); break;
            }
        } else {
            switch (protocol) {
                case IPPROTO_TCP: tcp_header->SrcPort = htons(port); break;
                case IPPROTO_UDP: udp_header->SrcPort = htons(port); break;
            }
        }
        WinDivertHelperCalcChecksums(packet, packet_len, &addr, 0);
        if (!WinDivertSend(handle, packet, packet_len, NULL, &addr)) {
            fprintf(stderr, "[!] warning: failed to reinject packet (%d)\n", GetLastError());
        }
        putchar('\n');
    }
}
