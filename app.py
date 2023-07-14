from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
from geet_slide3 import Geetest

app = Flask(__name__)

executor = ThreadPoolExecutor(10)


@app.route("/api/slide", methods=['GET', 'POST'])
def index():
    # 检查请求中是否包含challenge参数
    challenge = request.args.get('challenge')
    print(challenge)
    if not challenge:
        # 如果没有challenge参数，则返回错误JSON响应
        return jsonify(error='请求参数错误'), 400
    if len(challenge) != 32:
        return jsonify(error='请求参数错误'), 400
    # 在这里处理包含challenge参数的异步请求
    future = executor.submit(get_click, challenge)
    return future.result()


def get_click(challenge):
    slide = Geetest()
    res = slide.run(challenge)
    return {"data": res}


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)
