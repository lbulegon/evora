import json
from django.core.management.base import BaseCommand
from django.conf import settings
import openai


class Command(BaseCommand):
    help = "Envia uma pergunta para o modelo gpt-3.5-turbo da OpenAI e imprime a resposta formatada como JSON"

    def add_arguments(self, parser):
        parser.add_argument('mensagem', type=str, help='Texto a ser enviado para o ChatGPT')

    def handle(self, *args, **kwargs):
        pergunta = kwargs['mensagem']
        openai.api_key = settings.OPENAI_API_KEY

        try:
            resposta = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Você é um assistente inteligente."},
                    {"role": "user", "content": pergunta}
                ],
                temperature=0.7
            )

            conteudo = resposta['choices'][0]['message']['content']
            modelo = resposta['model']

            resultado = {
                "pergunta": pergunta,
                "resposta": conteudo.strip(),
                "modelo": modelo
            }

            print(json.dumps(resultado, indent=4, ensure_ascii=False))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Erro: {str(e)}"))
