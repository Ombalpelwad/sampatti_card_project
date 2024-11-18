import requests

def main():

    url = "https://conv.sampatticards.com/user/send_worker_salary_slips" 
    response = requests.post(url)
    if response.status_code == 200:
        print("Request successful:", response.json())
    else:
        print("Request failed:", response.status_code)

if __name__ == "__main__":
    main()
