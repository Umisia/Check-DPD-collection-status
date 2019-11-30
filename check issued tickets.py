from selenium import webdriver
import time, re, json, requests

clinetID = <clientid> #set value
clientSecret = <clientsecret> #set value

def getToken(code, clinetID, clientSecret):
    par = {
    'scope':'Desk.tickets.READ,Desk.search.READ,Desk.tickets.UPDATE',
    'client_id':clinetID,
    'response_type':'code',
    'access_type':'offline',
    'redirect_uri':'http://localhost:8080/',
    'grant_type':'authorization_code',
    'code': code,
    'client_secret':clientSecret'
    }
    req = requests.post("https://accounts.zoho.com/oauth/v2/token?", params= par)
    json_data = json.loads(req.text)
    token = json_data["refresh_token"]
    return token

def tokenRefresh(token, code, clinetID, clientSecret):
    par = {
    'refresh_token': token,
    'client_id': clinetID,
    'client_secret':clientSecret,
    'scope':'Desk.tickets.READ,Desk.search.READ,Desk.tickets.UPDATE',
    'redirect_uri':'http://localhost:8080/',
    'grant_type':'refresh_token',
    'code': code
    }
    req = requests.post("https://accounts.zoho.com/oauth/v2/token", params = par)
    json_refresh= json.loads(req.text)
    access_token_refreshed = json_refresh["access_token"]
    return access_token_refreshed

def searchIssued(access_token):
    status = "RMA Issued"
    orgID = <orgid> #set value

    head = {
    'orgId': orgID,
    'Authorization':'Zoho-oauthtoken '+ access_token,
    }
    response = requests.get("https://desk.zoho.com/api/v1/tickets/search?status=RMA Issued", headers = head)
    json_data = json.loads(response.text)
    return json_data

def checkDPDstatus(shipRef):
    browser.find_element_by_css_selector("#requestCode").send_keys(shipRef)
    browser.find_elements_by_class_name("submit_button_no_margin")[1].click()
    collectionStatus = browser.find_element_by_xpath("/html/body/div[2]/table[1]/tbody/tr[3]/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[3]").text
    browser.back()
    browser.find_element_by_css_selector("#requestCode").clear()
    return collectionStatus

def addComment(access_token, ticketID, dpdStatus):
    orgID = <orgid> #set value
    userID = <userid> #set value

    head = {
    'orgId': orgID,
    'Authorization':'Zoho-oauthtoken '+ access_token
    }
    data = {
      "isPublic" : "false",
      "contentType" : "html",
      "content" : "zsu[@user:"+ userID+ "]zsu DPD collection status: "+ dpdStatus + ". Please take action."
    }
    myJsonObject = json.dumps(data)
    requests.post("https://desk.zoho.com/api/v1/tickets/"+ ticketID +"/comments", headers = head, data = myJsonObject)
    return None

#launch and login to DPD account
url = "https://www.dpd.co.uk/reviewitv2/index.jsp"
browser = webdriver.Firefox()
browser.implicitly_wait(10)
browser.get(url)
browser.maximize_window()

DPD_username = <username> #set value
DPD_password = <password> #set value
browser.find_element_by_css_selector("#logon_username").send_keys(DPD_username)
browser.find_element_by_css_selector("#logon_password").send_keys(DPD_password)
browser.find_element_by_css_selector(".submit_button").click()
time.sleep(2)
browser.get("https://www.dpd.co.uk/reviewitv2/index.jsp")

#open new tab to get outh code
browser.execute_script('''window.open("https://accounts.zoho.com/developerconsole","_blank");''')
time.sleep(2)
browser.switch_to.window(browser.window_handles[1])

#login to Zoho account
Zoho_username = <username> #set value
Zoho_password = <password> #set value

browser.find_element_by_css_selector("#login_id").clear()
email = browser.find_element_by_css_selector("#login_id").send_keys(Zoho_username)
browser.find_element_by_css_selector("#nextbtn").click()
time.sleep(2)
password = browser.find_element_by_css_selector("#password").send_keys(Zoho_password)
browser.find_element_by_css_selector("#nextbtn").click()

time.sleep(2)

# get outh code
browser.find_element_by_css_selector("div.view_clients_rows:nth-child(2) > div:nth-child(4)").click()
browser.find_element_by_css_selector("div.view_clients_rows:nth-child(2) > div:nth-child(4) > div:nth-child(4) > div:nth-child(2) > div:nth-child(4)").click()
browser.find_element_by_css_selector(".add_client_form_field_value > input:nth-child(1)").send_keys("Desk.tickets.READ,Desk.search.READ,Desk.tickets.UPDATE")
browser.find_element_by_css_selector(".client_button_red").click()

code = browser.find_element_by_id("self_client_token_code").text
time.sleep(2)
browser.find_element_by_css_selector(".client_button_blue").click()

#logout
browser.find_element_by_css_selector("#ztb-profile-image").click()
browser.find_element_by_css_selector("#ztb-signout").click()
browser.execute_script('''window.close();''')
browser.switch_to.window(browser.window_handles[0])


access_token = getToken(code, clinetID, clientSecret)
token = tokenRefresh(access_token, code, clinetID, clientSecret)
tickets_data = searchIssued(token)

for index in range(len(tickets_data["data"])):
    shipRef = tickets_data["data"][index]["customFields"]["Shipping Reference In"]
    regex = re.compile('\d\d\d\d \d\d\d \d\d\d')
    if shipRef is not None and regex.match(shipRef) is not None:
        tickID = tickets_data["data"][index]["id"]
        tickNo = tickets_data["data"][index]["ticketNumber"]
        dpdStatus = checkDPDstatus(shipRef)
        firstWord = dpdStatus.split()[0]
        if firstWord != "Collected" and firstWord != "Accepted" and firstWord != "Created":
            print("Comment added: #", tickNo, dpdStatus)
            addComment(token, tickID, dpdStatus)


browser.close()
