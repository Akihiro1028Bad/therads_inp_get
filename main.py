import requests
import logging
from typing import List, Dict, Optional
import time
from datetime import datetime, timedelta

# ロギングの設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThreadsApiError(Exception):
    """Threads API関連のエラーを表すカスタム例外クラス"""
    pass

def make_api_request(url: str, params: Dict[str, str]) -> Dict:
    """
    APIリクエストを行い、結果を返す。エラーが発生した場合は適切に処理する。

    :param url: APIエンドポイントのURL
    :param params: リクエストパラメータ
    :return: APIレスポンスの辞書
    :raises ThreadsApiError: APIリクエストが失敗した場合
    """
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        error_info = {}
        if response.status_code == 400:
            try:
                error_info = response.json().get('error', {})
            except ValueError:
                pass
        
        if error_info:
            error_message = f"API request failed: {error_info.get('message', str(e))}"
            error_code = error_info.get('code')
            error_subcode = error_info.get('error_subcode')
            logger.error(f"{error_message} (Code: {error_code}, Subcode: {error_subcode})")
        else:
            logger.error(f"API request failed: {str(e)}")
        
        raise ThreadsApiError(f"API request to {url} failed")

def get_user_posts(access_token: str, days: int = 7, username: str = "Unknown") -> List[Dict]:
    """
    指定した日数分のユーザーの投稿を取得する

    :param access_token: アクセストークン
    :param days: 何日前までの投稿を取得するか
    :param username: ログ用のユーザー名
    :return: 投稿のリスト
    """
    logger.info(f"Fetching posts for user '{username}' for the last {days} days")
    url = "https://graph.threads.net/v1.0/me/threads"
    
    since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    until_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        "fields": "id,media_product_type,media_type,media_url,permalink,owner,username,text,timestamp,shortcode,thumbnail_url,children,is_quote_post",
        "since": since_date,
        "until": until_date,
        "limit": 100,  # 最大数を取得
        "access_token": access_token
    }

    try:
        data = make_api_request(url, params)
        posts = data.get("data", [])
        logger.info(f"Retrieved {len(posts)} posts for user '{username}'")
        return posts
    except ThreadsApiError:
        logger.error(f"Failed to fetch posts for user '{username}'")
        return []

def get_post_views(media_id: str, access_token: str, username: str = "Unknown") -> Optional[int]:
    """
    特定の投稿のビュー数を取得する

    :param media_id: 投稿のID
    :param access_token: アクセストークン
    :param username: ログ用のユーザー名
    :return: ビュー数、取得に失敗した場合はNone
    """
    logger.info(f"Fetching views for post {media_id} (User: '{username}')")
    url = f"https://graph.threads.net/v1.0/{media_id}/insights"
    params = {
        "metric": "views",
        "access_token": access_token
    }
    try:
        data = make_api_request(url, params)
        views = data["data"][0]["values"][0]["value"]
        logger.info(f"Post {media_id} has {views} views (User: '{username}')")
        return views
    except (ThreadsApiError, KeyError, IndexError):
        logger.error(f"Failed to fetch views for post {media_id} (User: '{username}')")
        return None

def get_average_impressions(access_token: str, days: int = 7, username: str = "Unknown") -> Optional[float]:
    """
    アカウントの平均インプレッション数を取得する

    :param access_token: アクセストークン
    :param days: 何日前までの投稿を対象とするか
    :param username: ログ用のユーザー名
    :return: 平均インプレッション数、取得に失敗した場合はNone
    """
    logger.info(f"Calculating average impressions for user '{username}' for the last {days} days")

    try:
        posts = get_user_posts(access_token, days, username)
        total_views = 0
        valid_post_count = 0

        for post in posts:
            views = get_post_views(post['id'], access_token, username)
            if views is not None:
                total_views += views
                valid_post_count += 1

            # API利用制限を避けるため、リクエスト間に少し待機時間を入れる
            time.sleep(0.5)

        if valid_post_count > 0:
            average_views = total_views / valid_post_count
            logger.info(f"Average impressions for user '{username}': {average_views:.2f} (based on {valid_post_count} posts)")
            return average_views
        else:
            logger.warning(f"No valid posts found to calculate average impressions for user '{username}'")
            return None

    except ThreadsApiError:
        logger.error(f"Failed to calculate average impressions for user '{username}'")
        return None

# 使用例
if __name__ == "__main__":
    access_token = "THQWJYTWRGUE80Y1gyZAFkyTUgzS1NIaXNTU0QyZA29rd2JZAM3NWQlp1TmxyMGUtaGlvS1VMTWZAjUFJTbEg2cS1zb0cxTW9xVnF4X0RsMHJNRHVqZAzhGb20xTnJRdldNcm5VQ2czdkNVMHZA2R1FabXRWMFRIWnBmTUZALVFNVcWUzRzFsMmNYNnB3"
    username = "konomi_bura"  # ログ用のユーザー名
    days = 7

    average_impressions = get_average_impressions(access_token, days, username)

    if average_impressions is not None:
        logger.info(f"Average Impressions for user '{username}' over the last {days} days: {average_impressions:.2f}")
    else:
        logger.error(f"Failed to retrieve average impressions for user '{username}'")