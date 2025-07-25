import subprocess
import socket
import nmap
from ldap3 import Server, Connection, ALL
from django.utils.timezone import now
#import ipaddress
from ..models import AdvancedEnumResult  # تأكد أن الموديل موجود

class DeepWideEnumerator:
    def __init__(self, target_ip, domain=None):
        self.target = target_ip
        self.domain = domain
        self.timestamp = now()
        self.result = {}

    def _run_cmd(self, cmd):
        try:
            return subprocess.getoutput(cmd)
        except Exception as e:
            return f"[!] Command error: {e}"
        
        

# def get_hostname_and_os(self):
#     try:
#         # إذا تم تمرير اسم، نحاول تحويله إلى IP
#         try:
#             ipaddress.ip_address(self.target)
#             ip = self.target
#         except ValueError:
#             ip = socket.gethostbyname(self.target)

#         hostname = socket.gethostbyaddr(ip)
#     except (socket.herror, socket.gaierror) as e:
#         hostname = ("Unknown", [], [self.target])
#         print(f"[!] Hostname resolution failed: {e}")

#     self.result["hostname"] = hostname[0]
#     self.result["aliases"] = hostname[1]
#     self.result["ip"] = hostname[2]
#     self.result["os_info"] = self._run_cmd(f"nmap -O {self.target}")


    def get_hostname_and_os(self):
        try:
            hostname = socket.gethostbyaddr(self.target)
        except socket.herror:
            hostname = ("Unknown", [], [self.target])
        self.result["hostname"] = hostname[0]
        self.result["aliases"] = hostname[1]
        self.result["ip"] = hostname[2]
        self.result["os_info"] = self._run_cmd(f"nmap -O {self.target}")

    def scan_ports_and_services(self):
        print("[*] Running full TCP port scan and service detection...")
        scanner = nmap.PortScanner()
        scanner.scan(self.target, arguments="-Pn -sS -sV -T4")
        ports = scanner[self.target].get("tcp", {}) if self.target in scanner.all_hosts() else {}
        self.result["open_ports"] = ports

    def enum_smb(self):
        print("[*] Enumerating SMB (shares, users)...")
        self.result["smbclient_shares"] = self._run_cmd(f"smbclient -L {self.target} -N")
        self.result["enum4linux"] = self._run_cmd(f"enum4linux -a {self.target}")
        self.result["rpcclient_users"] = self._run_cmd(f"rpcclient -N -U '' {self.target} -c enumdomusers")
        self.result["netbios"] = self._run_cmd(f"nmblookup -A {self.target}")

    def enum_snmp(self):
        print("[*] Enumerating SNMP if available...")
        self.result["snmpwalk"] = self._run_cmd(f"snmpwalk -v2c -c public {self.target}")

    def enum_ldap(self):
        print("[*] Enumerating LDAP...")
        try:
            server = Server(self.target, get_info=ALL)
            conn = Connection(server, auto_bind=True)
            conn.search('dc=example,dc=com', '(objectclass=person)', attributes=['cn'])
            self.result["ldap_users"] = [str(entry) for entry in conn.entries]
        except Exception as e:
            self.result["ldap_users"] = f"[!] LDAP Error: {e}"

    def enum_dns_zone_transfer(self):
        print("[*] Attempting DNS zone transfer...")
        self.result["dns_zone_transfer"] = self._run_cmd(f"dig axfr @{self.target} {self.domain}") if self.domain else "No domain provided"

    def enum_dirsearch(self):
        print("[*] Searching for hidden web paths...")
        self.result["dirsearch"] = self._run_cmd(f"dirsearch -u http://{self.target} -e php,html,js,asp")

    def run_all(self):
        self.get_hostname_and_os()
        self.scan_ports_and_services()
        self.enum_smb()
        self.enum_snmp()
        self.enum_ldap()
        self.enum_dns_zone_transfer()
        self.enum_dirsearch()
        self.save_to_db()
        return self.result

    def save_to_db(self):
        print("[*] Saving results to DB...")
        AdvancedEnumResult.objects.create(
            target=self.target,
            domain=self.domain or "",
            timestamp=self.timestamp,
            hostname=self.result.get("hostname"),
            os_info=self.result.get("os_info"),
            open_ports=self.result.get("open_ports"),
            smb_info=self.result.get("smbclient_shares"),
            enum4linux_output=self.result.get("enum4linux"),
            rpc_output=self.result.get("rpcclient_users"),
            netbios_info=self.result.get("netbios"),
            snmp_info=self.result.get("snmpwalk"),
            ldap_info=str(self.result.get("ldap_users")),
            dns_zone_transfer=self.result.get("dns_zone_transfer"),
            hidden_dirs=self.result.get("dirsearch"),
        )
