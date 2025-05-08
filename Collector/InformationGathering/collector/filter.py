import requests
from bs4 import BeautifulSoup

# Function to extract data from the Shodan HTML response
def extract_shodan_data(ip):
    url = f'https://www.shodan.io/host/{ip}'
    
    # Send the GET request to fetch the page content
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract general information
        general_info = {}
        general_info['country'] = soup.find('label', text='Country').find_next('div').get_text(strip=True)
        general_info['city'] = soup.find('label', text='City').find_next('div').get_text(strip=True)
        general_info['organization'] = soup.find('label', text='Organization').find_next('div').get_text(strip=True)
        general_info['isp'] = soup.find('label', text='ISP').find_next('div').get_text(strip=True)
        general_info['asn'] = soup.find('label', text='ASN').find_next('div').get_text(strip=True)
        general_info['os'] = soup.find('label', text='Operating System').find_next('div').get_text(strip=True)

        # Extract open ports
        open_ports = []
        ports_section = soup.find('div', {'id': 'ports'})
        if ports_section:
            open_ports = [port.get_text(strip=True) for port in ports_section.find_all('a')]

        # Extract other relevant data (e.g., services or products)
        services = []
        services_section = soup.find_all('h1', class_='banner-title')
        for service in services_section:
            service_name = service.find('em')
            if service_name:
                services.append(service_name.get_text(strip=True))
        
        # Extract hashes (if available)
        hashes = {}
        hashes_section = soup.find('div', class_='hashes-table')
        if hashes_section:
            for row in hashes_section.find_all('div'):
                hash_type = row.find_previous('div').get_text(strip=True) if row.find_previous('div') else ''
                if hash_type and row.get_text(strip=True):
                    hashes[hash_type] = row.get_text(strip=True)

        # Return all extracted data in a dictionary
        return {
            'ip': ip,
            'general_info': general_info,
            'open_ports': open_ports,
            'services': services,
            'hashes': hashes,
        }
    
    else:
        return {'error': f"Failed to retrieve data for IP: {ip}, Status Code: {response.status_code}"}

# Example Usage
ip = '45.74.4.179'
data = extract_shodan_data(ip)

# Print extracted data
if 'error' in data:
    print(data['error'])
else:
    print(f"IP: {data['ip']}")
    print("General Information:")
    for key, value in data['general_info'].items():
        print(f"  {key.capitalize()}: {value}")
    
    print("\nOpen Ports:")
    for port in data['open_ports']:
        print(f"  {port}")
    
    print("\nServices/Products:")
    for service in data['services']:
        print(f"  {service}")
    
    print("\nHashes:")
    for hash_type, hash_value in data['hashes'].items():
        print(f"  {hash_type}: {hash_value}")

