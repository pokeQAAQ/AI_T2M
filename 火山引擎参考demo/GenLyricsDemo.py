import json
import requests
import Sign

if __name__ == "__main__":
    ak = ""
    sk = ""
    prompt = "写一首关于烟花的歌"
    gender = "Female"
    genre = "Pop"
    mood = "Happy"

    action = "GenLyrics"
    version = "2024-08-12"
    region = "cn-beijing"
    service = 'imagination'
    host = "open.volcengineapi.com"
    path = "/"
    query = {'Action': action,
             'Version': version}
    body = {
        'Prompt': prompt,
        'Gender': gender,
        'Genre': genre,
        'Mood': mood,
    }
    x_content_sha256 = Sign.hash_sha256(json.dumps(body))
    headers = {"Content-Type": 'application/json',
               'Host': host,
               'X-Date': Sign.get_x_date(),
               'X-Content-Sha256': x_content_sha256
               }
    authorization = Sign.get_authorization("POST", headers=headers, query=query, service=service, region=region, ak=ak,
                                           sk=sk)
    print(f"===>authorization:{authorization}")
    headers["Authorization"] = authorization
    response = requests.post(Sign.get_url(host, path, action, version), data=json.dumps(body), headers=headers)
    print(f"===>Response:{response.text}")
