from urllib import request
import json

API = 'http://openapi.tuling123.com/openapi/api/v2'


def get_chat_response(user_id, text, config, logger):
    """
    调用图灵机器人接口，获取回复内容
    :return:
    """
    req_data = {
        "perception": {
            "inputText": {
                "text": text
            },
        },
        "userInfo": {
            "apiKey": config.TULING_APIKEY,
            "userId": str(user_id)
        }
    }

    req = request.Request(API,
                          data=json.dumps(req_data),
                          headers={'Content-Type': 'application/json'},
                          method='POST')
    resp = request.urlopen(req, timeout=180)
    resp_json = resp.read()
    resp_data = json.loads(resp_json)
    if 'results' not in resp_data:
        code = resp_data['intent']['code']
        logger.error('tuling code:{} uid:{} text:{}'.format(code, user_id, text))
        raise Exception
    else:
        #   {
        #     "intent": {
        #         "code": 10005,
        #         "intentName": "",
        #         "actionName": "",
        #         "parameters": {
        #             "nearby_place": "酒店"
        #         }
        #     },
        #     "results": [
        #         {
        #          	"groupType": 1,
        #             "resultType": "url",
        #             "values": {
        #                 "url": "http://m.elong.com/hotel/0101/nlist/#indate=2016-12-10&outdate=2016-12-11&keywords=%E4%BF%A1%E6%81%AF%E8%B7%AF"
        #             }
        #         },
        #         {
        #          	"groupType": 1,
        #             "resultType": "text",
        #             "values": {
        #                 "text": "亲，已帮你找到相关酒店信息"
        #             }
        #         }
        #     ]
        # }
        results = resp_data['results']
        for result in results:
            if result['resultType'] != 'text':
                continue
            else:
                return result['values']['text']
        return 'emmm...我竟不知道该说啥...'


