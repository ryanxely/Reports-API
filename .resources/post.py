import requests

files = [
    ('files', open('E:/Videos/0408(1).mp4','rb')),
    ('files', open('E:/Music/Anime songs/City Hunter - Super Girl.mp3','rb'))
    ]
data = {
    'title': 'Fucking',
    'text': 'Hello fuck you'
    }
headers = {'x-api-key': '98DE6A2D597F7CE8307B6FC1BA075ABC05026C3B7334322D'}

res = requests.post("http://localhost:500/reports/add", data=data, files=files, headers=headers)
print(res.json())
