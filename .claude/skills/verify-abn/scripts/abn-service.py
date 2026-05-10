import urllib.request as req

#Search parameters for ABRSearchByNameSimpleProtocol service
#Note, this service requires all parameters to be specified, even if you specify no query parameter
#The parameters specified below will search for an entity with  the name 'coles' with postcode '2250'
#In this case, unspecified search parameters all default to 'Y' 
#(i.e. will search for the legal & trading name 'coles' in all States and Territories
name = 'Coles'
postcode = ''
legalName = ''		
tradingName = ''	
NSW = 'Y'			
SA = 'N'				
ACT = 'N'			
VIC = 'N'			
WA = 'N'				
NT = 'N'				
QLD = 'N'			
TAS = 'N'

authenticationGuid = '13f789ba-3e0b-4193-b524-65348b3887d7'		#Your GUID should go here

#Constructs the URL by inserting the search parameters specified above
#GETs the url (using urllib.request.urlopen)
conn = req.urlopen('https://abr.business.gov.au/abrxmlsearchRPC/AbrXmlSearch.asmx/' + 
					'ABRSearchByNameSimpleProtocol?name=' + name + 
					'&postcode=' + postcode + '&legalName=' + legalName + 
					'&tradingName=' + tradingName + '&NSW=' + NSW + 
					'&SA=' + SA + '&ACT=' + ACT + '&VIC=' +  VIC + 
					'&WA=' + WA + '&NT=' + NT + '&QLD=' + QLD + 
					'&TAS=' + TAS + '&authenticationGuid=' + authenticationGuid)
					
#XML is returned by the webservice
#Put returned xml into variable 'returnedXML' 
#Output xml string to file 'output.xml' and print to console
returnedXML = conn.read()
f = open('output.xml', 'wb')
f.write(returnedXML)
f.close
print(returnedXML)
