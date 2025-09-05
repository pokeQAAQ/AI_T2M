import requests
import Sign

if __name__ == "__main__":
    ak = ""
    sk = ""

    action = "QueryUsage"
    version = "2024-08-12"
    region = "cn-beijing"
    service = 'imagination'
    host = "open.volcengineapi.com"
    path = "/"
    query = {'Action': action,
             'Version': version}
    # 这里get 请求没有body，传空字符串即可。
    x_content_sha256 = Sign.hash_sha256("")
    headers = {"Content-Type": 'application/json',
               'Host': host,
               'X-Date': Sign.get_x_date(),
               'X-Content-Sha256': x_content_sha256
               }
    authorization = Sign.get_authorization("GET", headers=headers, query=query, service=service, region=region, ak=ak,
                                           sk=sk)
    print(f"===>authorization:{authorization}")
    headers["Authorization"] = authorization
    response = requests.get(Sign.get_url(host, path, action, version), headers=headers)
    print(f"===>Response:{response.text}")
