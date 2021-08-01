import requests
from requests.sessions import session
import re
import base64
from PIL import Image
from io import BytesIO

# Nhập username
username = ""
# Nhập password
password = ""

# Chuột phải vào mở tài liệu online, chọn copy link address
download_urls = [
    "https://catalog.hvtc.edu.vn/F?func=service&doc_library=AOF01&local_base=AOF01&doc_number=000014191&sequence=000001&line_number=0001&func_code=DB_RECORDS&service_type=MEDIA",
]


def get_pages(session=None, max_page=1, jsp_id=None):
    images = []
    for page_number in range(1, max_page + 1):
        respond = session.get(
            url="http://catalog.hvtc.edu.vn:8080/ebook/view.jsp?id={}&&pages={}".format(
                jsp_id, page_number
            ),
        )
        respond_data = respond.text
        base64_images = re.findall(
            r"<img id=\"\d+\" alt style=\"margin:0 auto\" class=\"full_image img-responsive\" src=\"data:image/jpg;base64,(.*)\">",
            respond_data,
        )
        for base64_image in base64_images:
            images.append(Image.open(BytesIO(base64.b64decode(base64_image))))
    return images


session = requests.Session()
# get PDS ID
respond = session.post(
    url="https://catalog.hvtc.edu.vn/pds",
    headers={
        "referer": "https://catalog.hvtc.edu.vn/pds?func=load-login&calling_system=primo&institute=AOF01&lang=und&url=http://libsearch.hvtc.edu.vn:80/primo_library/libweb/pdsLogin?targetURL=http%3A%2F%2Flibsearch.hvtc.edu.vn%2Fprimo-explore%2Fsearch%3Fvid%3Daof%26fbclid%3DIwAR3PxziGm48VlfBQWwdXHxF3QKmVvu65GxL_2drz3dWiZrizCXZNSmKKfwM%26from-new-ui%3D1%26authenticationProfile%3DAOF"
    },
    data="func=login&calling_system=primo&term1=short&lang=vie&selfreg=&bor_id={}&bor_verification={}&institute=AOF50&url=http%3A%2F%2Flibsearch.hvtc.edu.vn%3A80%2Fprimo_library%2Flibweb%2FpdsLogin%3FtargetURL%3Dhttp%253A%252F%252Flibsearch%252Ehvtc%252Eedu%252Evn%252Fprimo-explore%252Fsearch%253Fvid%253Daof%26fbclid%3DIwAR3PxziGm48VlfBQWwdXHxF3QKmVvu65GxL%255F2drz3dWiZrizCXZNSmKKfwM%26from-new-ui%3D1%26authenticationProfile%3DAOF".format(
        username, password
    ),
)
pds_cookies = re.findall(r"pds_handle=(\d+)", respond.text)
if pds_cookies:

    # SET COOKIE AND HEADERS
    pds_cookie = pds_cookies[0]
    session.cookies.set("PDS_HANDLE", pds_cookie[0], domain=".hvtc.edu.vn", path="/")
    headers = {
        "Upgrade-Insecure-Requests": "1",
        "Host": "catalog.hvtc.edu.vn",
        "Connection": "close",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3",
        "Accept-Encoding": "gzip, deflate",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36",
    }

    for download_url in download_urls:
        if not re.search(
            r"https:\/\/catalog\.hvtc\.edu\.vn\/F\?func=.*&doc_library=.*&local_base=.*&doc_number=\d+&sequence=\d+&line_number=\d+&func_code=.*&service_type=.*",
            download_url,
        ):
            print("WRONG URL")
            continue
        doc_number = re.findall(r"&doc_number=(\d+)\&", download_url)[0]
        headers["Referer"] = "http://libsearch.hvtc.edu.vn/"
        respond = session.get(
            url=download_url,
            headers=headers,
        )
        pds_sso = re.findall(r"var url = '(.*)';", respond.text)

        headers["Referer"] = download_url
        respond = session.get(
            url=pds_sso[0].replace(":443", "", 1) if pds_sso else None,
            headers=headers,
        )
        sso = re.findall(r"<a href=\"(.*)\">", respond.text)[0]

        headers["Referer"] = pds_sso[0].replace(":443", "", 1) if pds_sso else None
        sso_url = "{}{}".format(
            "https://catalog.hvtc.edu.vn",
            "/goto/logon/https://catalog.hvtc.edu.vn:443/F/{}?func=service&amp=&amp=&amp=&amp=&amp=&amp=&amp=&doc%5Flibrary=AOF01&local%5Fbase=AOF01&doc%5Fnumber={}&sequence=000001&line%5Fnumber=0001&func%5Fcode=DB%5FRECORDS&service%5Ftype=MEDIA&pds_handle={}".format(
                re.findall(r"\/F\/(.*)\?func=service", sso)[0], doc_number, pds_cookie
            ),
        )
        respond = session.get(
            url=sso_url,
            headers=headers,
        )

        alephUrl = re.findall(r'name="alephUrl" value="(.*)"\/>', respond.text)[0]
        del headers["Referer"]
        headers["Orgin"] = "null"
        headers["Host"] = "catalog.hvtc.edu.vn:8080"
        respond = session.post(
            url="http://catalog.hvtc.edu.vn:8080/ebook/",
            data=dict(
                {
                    "alephUrl": alephUrl,
                    "alephUri": "https://catalog.hvtc.edu.vn/F/{}?func=service&amp=&amp=&amp=&amp=&amp=&amp=&amp=&doc%5Flibrary=AOF01&local%5Fbase=AOF01&doc%5Fnumber={}&sequence=000001&line%5Fnumber=0001&func%5Fcode=DB%5FRECORDS&service%5Ftype=MEDIA&pds_handle={}".format(
                        re.findall(r"\/F\/(.*)\?func=service", sso)[0],
                        doc_number,
                        pds_cookie,
                    ),
                }
            ),
            headers=headers,
        )
        # JSP ID
        jsp_id = re.findall(r"<a href=\"view\.jsp\?id=(\d+)\"", respond.text)[0]

        # ACCESS JSP READER
        respond = session.get(
            url="http://catalog.hvtc.edu.vn:8080/ebook/view.jsp?id={}".format(jsp_id),
        )
        respond_data = respond.text
        pages = re.findall(r"<a href=\"view\.jsp\?id=\d+&&pages=(\d+)\">", respond_data)
        max_page = max(
            [int(page_number) for page_number in pages]
            if pages
            else [
                1,
            ]
        )
        images = get_pages(session=session, max_page=max_page, jsp_id=jsp_id)
        images[0].save(
            "{}.pdf".format(re.findall(r"&doc_number=(\d+)\&", download_url)[0]),
            "PDF",
            resolution=100.0,
            save_all=len(images) > 1,
            append_images=images[1:] if len(images) > 1 else None,
        )
else:
    print("No")

    # respond = session.get(
    #     url="{}{}".format(
    #         "https://catalog.hvtc.edu.vn",
    #         directory_url[0] if directory_url else directory_url,
    #     ),
    #     headers={"referer": sso_url[0].replace(":443", "") if sso_url else None},
    # )
    # print(respond.text)
