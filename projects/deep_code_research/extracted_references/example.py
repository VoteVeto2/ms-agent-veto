
    import requests
    from typing import List

    class UserClient:
        def get_users(self) -> List[dict]:
            return requests.get('/users').json()
    