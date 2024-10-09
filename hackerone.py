import requests
import os
import re  # Import regex library for domain extraction

auth = ('username', 'api_key')
h2 = ""
script_dir = os.path.dirname(os.path.abspath(__file__))

def getAllPrograms():
    global auth
    global h2
    for i in range(1, 7):
        headers = {'Accept': 'application/json'}
        try:
            print(f"Fetching page {i} of programs...")
            r = requests.get(
                f'https://api.hackerone.com/v1/hackers/programs?page[size]=100&page[number]={i}',
                auth=auth,
                headers=headers,
                timeout=10  # Set a timeout for the request
            )
            r.raise_for_status()  # Raise an error for bad responses
            programs = r.json().get("data", [])
            print(f"Found {len(programs)} programs on page {i}.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching programs on page {i}: {e}")
            continue  # Skip to the next page if there's an error

        for program in programs:
            if program["attributes"]["offers_bounties"]:
                text = "Name: " + str(program["attributes"]["name"]) + "\n"
                text += "Handle: " + str(program["attributes"]["handle"]) + "\n"
                text += "Valid Reports For User: " + str(program["attributes"]["number_of_valid_reports_for_user"]) + "\n"
                text += "Start accepting at: " + str(program["attributes"]["started_accepting_at"]) + "\n"
                text += "Mode: " + str(program["attributes"]["state"]) + "\n"
                text += "Accept Submission: " + str(program["attributes"]["submission_state"]) + "\n"
                text += "Allow Splitting: " + str(program["attributes"].get("allow_bounty_splitting", "N/A")) + "\n"
                text += "MCurrency: " + str(program["attributes"]["currency"]) + "\n"
                h2 += text + "\n"  # Append program details to global h2
                getAssets(str(program["attributes"]["handle"]), text)

def getAssets(handle, text):
    global h2
    global auth
    text2 = ""
    headers = {'Accept': 'application/json'}
    
    # Define the year range
    years = [str(year) for year in range(2000, 2025)]

    try:
        print(f"Fetching assets for handle {handle}...")
        r = requests.get(
            f'https://api.hackerone.com/v1/hackers/programs/{handle}',
            auth=auth,
            headers=headers,
            timeout=10
        )
        r.raise_for_status()  # Raise an error for bad responses
        response_json = r.json()
        scopes = response_json["relationships"]["structured_scopes"]["data"]
        
        # Iterate through scopes and filter based on the defined years
        for scope in scopes:
            created_at = scope["attributes"]["created_at"]
            updated_at = scope["attributes"]["updated_at"]
            if scope["attributes"]["eligible_for_bounty"] and (
                any(year in created_at for year in years) or
                any(year in updated_at for year in years)
            ):
                text2 += scope["attributes"]["asset_identifier"] + "\n"
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching assets for handle {handle}: {e}")
    except KeyError as e:
        print(f"Unexpected data structure for handle {handle}: {e}")
    
    if text2:
        h2 += text2 + "\n"  # Append asset identifiers to global h2
        print(f"Assets for {handle}:\n{text2}")

def writeResults():
    global h2
    global script_dir

    wildcards = []
    domains = []
    subdomains = []

    domain_pattern = re.compile(
        r"(?:(?P<wildcard>\*\.)?(?P<domain>[a-zA-Z0-9-]+\.)+(?P<tld>[a-zA-Z]{2,}))"
    )

    c = h2.splitlines()

    for line in c:
        for match in domain_pattern.finditer(line):
            if match.group("wildcard"):
                wildcards.append(match.group(0))
            else:
                domain_parts = match.group(0).split('.')
                if len(domain_parts) > 2:
                    subdomains.append(match.group(0))
                else:
                    domains.append(match.group(0))

    wildcards = list(set(wildcards))
    domains = list(set(domains))
    subdomains = list(set(subdomains))

    print(f"Found {len(wildcards)} wildcards, {len(domains)} domains, and {len(subdomains)} subdomains.")
    
    # Use UTF-8 encoding to handle Unicode characters
    with open(os.path.join(script_dir, 'program_details.txt'), "w", encoding="utf-8") as f:
        f.write(h2)
    with open(os.path.join(script_dir, 'wildcards.txt'), "w", encoding="utf-8") as f:
        f.write("\n".join(wildcards))
    with open(os.path.join(script_dir, 'domains.txt'), "w", encoding="utf-8") as f:
        f.write("\n".join(domains))
    with open(os.path.join(script_dir, 'subdomains.txt'), "w", encoding="utf-8") as f:
        f.write("\n".join(subdomains))

    print("Writing results to files...")

getAllPrograms()
writeResults()
