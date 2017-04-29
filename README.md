# MS17-010
MS17-010 is the Microsoft security bulletin which fixes several remote code execution vulnerabilities in the SMB service on Windows systems.

There are numerous things about MS17-010 that make it esoteric, such as manipulating the Windows kernel pool heap allocations, running Windows ring 0 shellcode, and the intricacies of the SMB protocol.

## Scanners
There is a Metasploit scanner and a Python port. The scanner are able to use uncredentialed information leakage to determine if the MS17-010 patch is installed on a host. If it is not installed, it will also check for DoublePulsar infections.

## Exploits
There is a Python script and a replay file that has reliably been shown to infect Windows Server 2008 R2 SP1 with DoublePulsar.

## Payloads
Windows ring 0 shellcode is being crafted so that instead of DoublePulsar, the transition from ring 0 to ring 3 and running usermode payloads is done in a single step.

## Resources 
- https://zerosum0x0.blogspot.com/2017/04/doublepulsar-initial-smb-backdoor-ring.html
- https://www.rapid7.com/db/modules/auxiliary/scanner/smb/smb_ms17_010

### Credits
- @zerosum0x0
- @jennamagius
- @nixawk

### Acknowledgements
- Shadow Brokers
- Equation Group
- skape
- Stephen Fewer