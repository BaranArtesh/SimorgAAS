<<<<<<< HEAD
#Top li te keve

#JEHIR
import socket 
import request

def get_ip_info(target):
    try:
        ip_address = socket.gethostbyname(target)
        response = request.get(f"https://ipinfo.io/{ip_address}/json")
        data = response.json()

        ip_info ={

            "IP ADDRESS": data.get("ip", N/A),
            "HOSTNAME": target,
            "CITY": data.get("city", N/A)
        }
        return ip_info
=======
#xwelisere te be
>>>>>>> 0cbf5ba1140f9aca8ab19033034e8cd80948658e
