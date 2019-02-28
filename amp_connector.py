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
sleep_time = 10


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
		print('\n      .:|:.:|:.')
		print('AMP4E Endpoint Cleaner\n')
		get_tenants()
		print(str(len(tenants)) + " tenant(s) are registered")
		print(str(sleep_time) + " seconds between checks")
		print("______________________________________\n")

		for tenant in tenants:
			print("Tenant: " + tenant)
			client_id = tenant
			api_key = tenants[tenant][0]
			auth_string = "https://{}:{}@api.amp.cisco.com".format(client_id, api_key)
			age_limit = tenants[tenant][1]
			print("Timed out: " + str(age_limit) + " days since last seen")
			action = tenants[tenant][2]
			group = tenants[tenant][3]
			print("Retrieving endpoints...")
			json_data = get_json_endpoints(auth_string)
			endpoints = get_endpoints(json_data)
			print("Processing endpoints...")

			processed_ep = clean_ep(endpoints, age_limit, group)
			print(str(len(processed_ep)) + " endpoints has timed out")
			#print(processed_ep)
			log_endpoints(processed_ep,tenant)
			#print(action)
			if (action == "delete"):
				#delete_endpoints(old, auth_string)
				pass

			elif (action == "log"):
				log_endpoints(old, client_id)
			print("Job finished!")
			print("______________________________________\n")

			#print(processed_ep)

			#print("Endpoints processed: " + str(processed_ep))

		print("\nWaiting for next check \n")

		spinner = spinning_cursor()
		current_time = datetime.now()
		sleep_start = current_time

		while (int((current_time - sleep_start).total_seconds()) < sleep_time):

			for _ in range(9):
					sys.stdout.write(next(spinner))
					sys.stdout.flush()
					time.sleep(1)
					sys.stdout.write("\a")

			
			sys.stdout.write("\r         ")
			sys.stdout.write("\r")
			
			#sys.stdout.flush()
			current_time = datetime.now()


def get_tenants():
	
	config_path = "config.ini"
	config = ConfigParser.ConfigParser()
	config.read(config_path)
	global tenants 

	for section in config.sections():

		client_id = config.get(str(section), "clientID")
		api_key = config.get(str(section), "apiKey")
		age_limit = config.get(str(section), "age_limit")
		group = config.get(str(section), "group")
		action = config.get(str(section), "action")
		tenants[client_id] = [api_key, int(age_limit), group, action] 

def spinning_cursor(): #Cisco Loading bar
	while True:
		for cursor in '.:|:.:|:.':
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
	inactive_days = None

	for ep in endpoints:
		guid = endpoints[ep]
		last_seen = datetime.strptime(guid[0], '%Y-%m-%dT%H:%M:%SZ')
		#print(last_seen)
		group = guid[1]
		inactive_days = (current_time - last_seen).days
		#print(inactive_days)

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

	f= open("logs/expired_endpoints_" + tenant + "_" + str(datetime.now()) + ".txt","w+")
	print("Logging timed out endpoints...")

	for ep in endpoints:
		f.write("Endpoint: " + ep + "\n")

	f.close() 

	print("Logged " + str(len(endpoints)) + " endpoints")
	#print("Wrote to file for tenant " + tenant)  


#RETURN NONE
def delete_endpoints(endpoints, auth_string):

	print("Deleting timed out endpoints...")
	for guid in endpoints:
		url = auth_string + "/v1/computers/" + guid
		#print guid
		response =  requests.request("DELETE", url)
	print("Deleted " + str(len(endpoints)) + " endpoints from portal")

if __name__ == '__main__':
	main()
