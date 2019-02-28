#This python script is intended to delete duplicated AMP for EndPoint hostnames.

#The script executes as follows: Enter AMP4E - API Credentials -> Search all hostnames -> Create hostname duplicate list -> Query duplicate install date -> delete dated hostname. After the script runs, check AMP4E Console > Accounts > Audit Log, for changes the script performed.

#Authors: Max Wijnbladh and Chris Maxwell

import json
import requests
import urllib3
from datetime import datetime
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import os
import sys
import time
import ConfigParser

#parameters:

tenants = {} #dict where key is client id and value is API key [api_key, age_limit, groups]
sleep_time = 5


def get_json_endpoints(auth_string):

	url = auth_string + "/v1/computers" #JSON parse data
	r =  requests.request("GET", url)
	if r.status_code == 200:
		json_data = r.json()
		return json_data
	else:
		print ("Unable to authenticate, response code: {}".format(r.status_code))
		exit()

#script main start
def main():


	while(1):
		os.system("clear")
		print("______________________________________")
		print('\nAMP4E Endpoint Cleaner')
		print("______________________________________\n")
		print("Getting endpoints")
		#spinner = spinning_cursor()
		#for _ in range(5):
		#		sys.stdout.write(next(spinner))
		#		sys.stdout.flush()
		#		time.sleep(0.5)
		#		sys.stdout.write("\a")

		get_tenants()
		print("Tenants:" + str(tenants))


		for tenant in tenants:
			print("Tenant " + tenant)
			client_id = tenant
			api_key = tenants[tenant][0]
			auth_string = "https://{}:{}@api.amp.cisco.com".format(client_id, api_key)
			age_limit = tenants[tenant][1]
			action = tenants[tenant][2]
			group = tenants[tenant][3]

			json_data = get_json_endpoints(auth_string)
			endpoints = get_endpoints(json_data)
			print("Finding inactive entries")

			processed_ep = clean_ep(endpoints, age_limit, group)
			#print(processed_ep)
			log_endpoints(processed_ep,tenant)
			print(action)
			if (action == "delete"):
				#delete_endpoints(old, auth_string)
				pass

			elif (action == "log"):
				log_endpoints(old, client_id)

			print(processed_ep)

			print("Endpoints processed: " + str(processed_ep))

		print("\nWaiting for next scan")




		time.sleep(sleep_time)


def get_tenants():
	
	config_path = "config.ini"
	config = ConfigParser.ConfigParser()
	config.read(config_path)
	global tenants 
	i = 1

	try:
		while (i < 5):
			print(i)
			client_id = config.get("Tenant " + str(i), "clientID")
			api_key = config.get("Tenant " + str(i), "apiKey")
			age_limit = config.get("Tenant " + str(i), "age_limit")
			group = config.get("Tenant " + str(i), "group")
			action = config.get("Tenant " + str(i), "action")
			tenants[client_id] = [api_key, age_limit, group, action] 

			i = i + 1
	except Exception as e:
		print(e)
		print("end of config file all good")



def init_params():
    """
    Screen which allows the user to choose how to enter parameters for the script runtime.
    current options are by entering the information manually, or by reading them from the config.ini
    file.

    """
    config_path = "config.ini"
    global client_id
    global api_key
    global sleep_time

    print("______________________________________")
    print('\nAMP4E Duplicate Fixer')
    print("______________________________________\n")

    op = raw_input("Enter settings manually? [y/n]")

    if (op == "y"):

        temp = raw_input("Client ID:")
        if (temp != ""):
            client_id = temp

        temp = raw_input("API Key:")
        if (temp != ""):
            api_key = temp

        temp = raw_input("Scanning Interval (hours):")
        if (temp != ""):
            sleep_time = float(temp) * 60

    elif (op == "n"):
		temp = raw_input("Enter relative path to config file ['/config.ini']")
		if (temp != ""):
			config_path = temp
		config = ConfigParser.ConfigParser()
		config.read(config_path)

		client_id = config.get("Parameters", "clientID")
		api_key = config.get("Parameters", "apiKey")
		sleep_time = config.get("Parameters", "scanInterval")
		sleep_time = float(sleep_time) * 60
		auth_string  = "https://{}:{}@api.amp.cisco.com".format(client_id, api_key)

def spinning_cursor(): #Cisco Loading bar
	while True:
		for cursor in '.:|:.':
			yield cursor

def authenticate(client_id, api_key): #Authenticate with AMP4E API Credentials

	auth_string = "https://{}:{}@api.amp.cisco.com".format(client_id, api_key)
	#print (auth_string)

	url = auth_string + "/v1/computers" #JSON parse data
	r =  requests.request("GET", url)
	if r.status_code == 200:
		print(" Successfully authenticated you with the AMP Console!")
		json_data = r.json()
		return json_data
	else:
		print (" Unable to authenticate you with the AMP Console, response code: {}".format(r.status_code))
		exit()


def get_endpoints(json_data): #RETURNS: dict[guid]=[hostname,install date]
	endpoints = {}

	#get all endpoints stored in amp portal
	for host in json_data["data"]:
		endpoints[host["connector_guid"]] = [host["last_seen"], host["group_guid"]]
		#print(endpoints[host["connector_guid"]])

	return endpoints #create dict with all endpoints


#RETURN dict
def clean_ep(endpoints, age_limit, groups):

	old = []
	current_time = datetime.now()
	inactive_time = None

	for ep in endpoints:
		guid = endpoints[ep]
		last_seen = datetime.strptime(guid[0], '%Y-%m-%dT%H:%M:%SZ')
		print(last_seen)
		group = guid[1]
		inactive_days = (current_time - last_seen).total_seconds()

		#if (inactive_days > age_limit and group in groups):
		if (inactive_days > age_limit):
			#print(str(datetime.strptime(age, '%Y-%m-%dT%H:%M:%SZ')) + "is younger than " + str(youngest[key][1]))
			old.append(group)
		else:
			#print(str(datetime.strptime(age, '%Y-%m-%dT%H:%M:%SZ')) + "is older than " + str(youngest[key][1]))
			pass
	#print(old)
	return old


def log_endpoints(endpoints, tenant):

	f= open("expired_endpoints_"+ tenant +".txt","w+")

	for ep in endpoints:
		f.write("Endpoint: " + ep + "\n")

	f.close() 
	print("Wrote to file for tenant " + tenant)  


#RETURN NONE
def delete_endpoints(endpoints, auth_string):

	for guid in endpoints:
		url = auth_string + "/v1/computers/" + guid
		print guid
		response =  requests.request("DELETE", url)

if __name__ == '__main__':
	main()
