import random
import requests
import config


class Qiwi:
    def __init__(self, token, login):
        self.token = token
        self.login = login

    def get_payment_history(self):
        session = requests.Session()
        session.headers['authorization'] = 'Bearer ' + self.token
        payment_history = session.get('https://edge.qiwi.com/payment-history/v2/persons/' +
                                      self.login + '/payments', params={'rows': 50})
        payment_history = payment_history.json()
        return payment_history

    def generate_payment_code(self, user_id):
        return str(user_id) + ''.join(
            [str(random.choice(range(10))) for _ in range(4)]
        )

    def get_qiwi_payment_url(self, count):
        url = f"https://qiwi.com/payment/form/99999?extra%5B%27account" \
              f"%27%5D={config.qiwi_username}&extra%5B%27comment%27%5D=42345&amountInteger={count}" \
              "&amountFraction=0&currency=643&blocked[0]=sum&blocked[1]=account&" \
              "blocked[2]=comment&extra%5B%27accountType%27%5D=nickname"
        return url
