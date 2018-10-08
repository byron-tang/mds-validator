import argparse
import jsonschema
from jsonschema import Draft4Validator
import requests
import pandas as pd

MDS_SCHEMA_PATH ="https://raw.githubusercontent.com/CityOfLosAngeles/mobility-data-specification/dev/provider/"



class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class ProviderNotFoundError(Error):
    """
    Provider not found
    """

    def __init__(self, expression, message):
        self.expression = expression 
        self.message = message

class MDSProviderApi(): 
    """
    Class representing an MDS provider API
    """

    def _get_mds_url(self):
        df = pd.read_csv('https://raw.githubusercontent.com/CityOfLosAngeles/mobility-data-specification/dev/providers.csv')
        providers = df.to_dict(orient='records')
        for provider in providers:
            if provider['provider_name'].lower() == self.name.lower():
                return provider['mds_api_url']
        names = str([x['provider_name'] for x in providers])
        msg = "Provider {} not in list of providers {}".format(self.name, names)
        raise ProviderNotFoundError("ProviderNotFoundError", msg)

    def validate_trips(self): 
        """
        Validates the trips endpoint
        """
        r = requests.get(MDS_SCHEMA_PATH + "trips.json")
        schema = r.json()
        v = Draft4Validator(schema)
        token =  "Bearer " + self.token

        header = {'Authorization': token}
        r  = requests.get(self._get_mds_url() + self.post_fix + '/trips', headers=header)
        json = r.json()
        try: 
            jsonschema.validate(json,schema)
        except jsonschema.exceptions.ValidationError:
           for error in sorted(v.iter_errors(json), key=str):
               print(error)

    def validate_status_changes(self):
        """
        Validates the status_change endpoint
        """
        r = requests.get(MDS_SCHEMA_PATH + "status_changes.json")
        schema = r.json()
        v = Draft4Validator(schema)
        token =  "Bearer " + self.token

        header = {'Authorization': token}
        r  = requests.get(self._get_mds_url() + self.post_fix + '/status_changes', headers=header)
        json = r.json()
        try: 
            jsonschema.validate(json,schema)
        except jsonschema.exceptions.ValidationError:
            print("Validation error encounted for {}".format(r.url))
            for error in sorted(v.iter_errors(json), key=str):
                print(error)


    def __init__(self, name, token, post_fix):
        self.name = name
        self.token = token
        self.post_fix = post_fix
        self.header = {'Authorization': "Bearer " + self.token}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provide an MDS API to validate')
    parser.add_argument("--provider-name",type=str,
                        help="Name of the Provider that you are attempt to validate")

    parser.add_argument("--token",type=str,
                        help="Bearer Token for the provider that you are attempting to validate")
    parser.add_argument("--postfix", type=str,
                        help="if it exists, the post_fix (ie, city or version or both) from the MDS base url in providers.csv")
    

    parser.add_argument('--status-changes', dest='status_change', action='store_true')
    parser.add_argument('--trips', dest='trips', action='store_true')
    parser.set_defaults(status_change=False)
    parser.set_defaults(trips=False)
    args = parser.parse_args()
    if args.postfix: 
        api = MDSProviderApi(args.provider_name,args.token, args.postfix)
    else: 
        api = MDSProviderApi(args.provider_name, args.token, '')
    print("Attempting to validate {}".format(api.name))
    if args.trips:
        api.validate_trips()
    elif args.status_change:
        api.validate_status_changes()
    else: 
        api.validate_trips()
        api.validate_status_changes()
