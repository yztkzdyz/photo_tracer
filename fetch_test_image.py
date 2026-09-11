import requests

for name in ["lena.jpg", "messi5.jpg", "fruits.jpg", "avengers.jpg"]:
    url = f"https://raw.githubusercontent.com/opencv/opencv/master/samples/data/{name}"
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        open("input/test.jpg", "wb").write(r.content)
        print("OK", name, len(r.content), "bytes")
        break
    except Exception as e:
        print("fail", name, e)
else:
    print("all failed")
