import csv
import logging

from dotenv import load_dotenv
from os import getenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from time import sleep
from urllib3.exceptions import ProtocolError, MaxRetryError

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO) # Ou level=logging.DEBUG

logging.info('Carregando as variáveis de ambiente.')
load_dotenv(override=True)


def login(driver):
    url_login = 'https://accounts.descomplica.com.br/'
    logging.info(f'Acessando site de login: {url_login}')
    driver.get(url_login)

    logging.info('Captura as input box usuário e senha e também o botão de login.')
    username = driver.find_element(By.ID, 'signin-email')
    password = driver.find_element(By.ID, 'signin-password')
    button_login = driver.find_element(By.ID, 'signin-button')
    
    logging.info('Inserindo usuário e senha.')
    username.clear()
    password.clear()
    username.send_keys(getenv('USERNAME'))
    password.send_keys(getenv('PASSWORD'))

    logging.info('Clicando no botão "Entrar".')
    button_login.click()

    mensagem_erro_login_senha = 'Email e/ou senha informados são inválidos'
    logging.info(f'Verificando se a mensagem de mensagem "{mensagem_erro_login_senha}" sugir na tela.')
    try:
        xpath = '/html/body/div[3]/div/div/div[2]/div/div/div[3]/div/div/div[1]/div'
        wait_EC = EC.text_to_be_present_in_element((By.XPATH, xpath), mensagem_erro_login_senha)
        erro_login_senha = WebDriverWait(driver, 2).until(wait_EC)
        if erro_login_senha:
            logging.error(mensagem_erro_login_senha)
            logging.error('Encerrradno a execução do script.')
            raise SystemExit(0)

    except SystemExit: close(driver)
    except: pass


def logout(driver):
    def clicando_perfil():
        logging.info('Clicando no icon do perfil.')
        xpath = '/html/body/div[2]/div[1]/div[1]/div/div[1]/div[1]/ul/li[4]'
        wait_EC = EC.presence_of_element_located((By.XPATH, xpath))
        botao_perfil = WebDriverWait(driver, 15).until(wait_EC)
        botao_perfil.click()

    def clicando_sair():
        # Hoverable Dropdown - Como debugar javascript dentro do chrome
        # DevTools => Console => 'setTimeout(() => {debugger}, 3000)'
        logging.info('Clicando no icon de "Sair".')
        xpath = '/html/body/div[2]/div[1]/div[1]/div/div[1]/div[1]/ul/li[4]/div[2]/div[2]/ul/div/li[2]'
        wait_EC = EC.text_to_be_present_in_element((By.XPATH,xpath), 'Sair')
        WebDriverWait(driver, 15).until(wait_EC)
        driver.find_element(By.XPATH, xpath).click()

    try:
        clicando_perfil()
        clicando_sair()

    except (TimeoutException, NoSuchElementException):
        logging.error('Nova tentativa.')
        clicando_perfil()
        clicando_sair()


def close(driver):
    logging.info('Encerando o Selenium WebDriver.')
    driver.close()

    if getenv('REMOTE_WEBDRIVER'):
        logging.info(f'Desconectado do REMOTE WEBDRIVE.')
        driver.quit()

    logging.info('Encerrradno a execução do script.')
    exit()


def url_disciplinas(driver):
    logging.info('Acessando a URL com as "Disciplinas".')
    url = getenv('URL_DISCIPLINAS')
    driver.get(url)

    logging.info('Aguardando carregar o icone "D" no canto superior esquerdo para confirmar que o login ocorreu com sucesso.')
    try:
        css_selector = 'svg.icon-svg.menu-button__icon.menu-button__icon--right'
        wait_EC = EC.presence_of_element_located((By.CSS_SELECTOR, css_selector))
        WebDriverWait(driver, 60).until(wait_EC)
        logging.info('Login ocorreu com sucesso.')
    except:
        logging.exception('Logando o motivo do exception.')
        close(driver)


def launch_driver():

    def launch_remote_webdriver(remote_webdriver, options):
        try:
            logging.info(f'Conectando ao container selenium/standalone-chrome: {remote_webdriver}.')
            return webdriver.Remote(
                command_executor=remote_webdriver,
                options=options)

        except (MaxRetryError, ProtocolError) as e:
            logging.exception('Erro ao iniciar REMOTE WEBDRIVER.')
            if e:
                try: mensage = e.msg
                except: mensage = e
                logging.error(f'Mais detalhes sobre o erro: {mensage}')
            logging.info('Encerrradno a execução do script.')
            exit()

        except:
            logging.exception('Erro ao iniciar REMOTE WEBDRIVER.')
            logging.info('Encerrradno a execução do script.')
            exit()

    match getenv('BROWSER').lower():
        case 'chrome':
            options = webdriver.ChromeOptions()
            options.add_argument('--start-maximized')

            if getenv('REMOTE_WEBDRIVER'):
                logging.info('Iniciando REMOTE WEBDRIVER Chrome.')
                remote_webdriver = getenv('REMOTE_WEBDRIVER')
                return launch_remote_webdriver(remote_webdriver, options)

            else:
                logging.info('Iniciando WEBDRIVER Chrome.')
                return webdriver.Chrome(options=options)

        case 'firefox':
            options = webdriver.FirefoxOptions()
            options.add_argument('--start-maximized')

            if getenv('REMOTE_WEBDRIVER'):
                logging.info('Iniciando REMOTE WEBDRIVER Firefox.')
                remote_webdriver = getenv('REMOTE_WEBDRIVER')
                return launch_remote_webdriver(remote_webdriver, options)

            else:
                logging.info('Iniciando WEBDRIVER Firefox.')
                return webdriver.Firefox(options=options)


def gera_minutagem(driver):
    # class="classrooms__left" - Todos os modulos e itens
    # class="h3 classrooms__header" - Todos os modulos
    # class="classrooms__item" - todas as materias
    # class="classroom__list" - todas as aulas

    def get_all_modulos_name():
        output = []
        logging.info('Obtendo todos os nomes dos modulos.')
        div_modulos_itens = driver.find_element(By.CLASS_NAME, 'classrooms__left')
        div_modulos_itens = div_modulos_itens.find_elements(By.XPATH, 'div')
        for div in div_modulos_itens:
            nome_modulo = div.find_element(By.XPATH, './h3').text
            logging.info(f'Nome do Modulo: {nome_modulo}')
            output.append((nome_modulo))
        return output

    def get_all_materias_name(all_modulos_name):
        output = []
        logging.info('Obtendo todos os nomes das matérias.')
        for nome_modulo in all_modulos_name:
            # O nome do módulo tem espaços no início e no final da palavra
            h3_nome_modulo = driver.find_element(By.XPATH, f'//h3[text()=" {nome_modulo} "]')
            lis_materia = h3_nome_modulo.find_elements(By.XPATH, 'following-sibling::ul/li')
            for li_materia in lis_materia:
                nome_materia = li_materia.find_element(By.XPATH, './/h3').text
                logging.info(f'Modulo: {nome_modulo}, Matéria: {nome_materia}.')
                output.append((nome_modulo, nome_materia))
        return output

    def get_all_aulas_tempo(all_materias_name):
        output = []

        logging.info('Obtendo todos a aulas.')
        for materia_name in all_materias_name:
            nome_modulo = materia_name[0]
            nome_materia = materia_name[1]

            logging.info('Aguarda a página com as matérias  carregar.')
            sleep(5)

            logging.info(f'Clicando na matéria {nome_materia}.')
            # driver.find_element(By.XPATH, f'//h3[text()="{nome_materia}"]').click()
            wait_EC = EC.presence_of_element_located((By.XPATH, f'//h3[text()="{nome_materia}"]'))
            WebDriverWait(driver, 15).until(wait_EC).click()

            logging.info('Aguarda a página com as aulas carregar.')
            sleep(5)

            all_aulas_name =  [nome.text for nome in driver.find_elements(By.XPATH, '//h3')]
            url_aulas = driver.current_url

            for aula_name in all_aulas_name:

                logging.info(f'Clicando na aula {aula_name}.')
                # driver.find_element(By.XPATH, f'//h3[normalize-space()="{aula_name}"]').click()
                wait_EC = EC.presence_of_element_located((By.XPATH, f'//h3[normalize-space()="{aula_name}"]'))
                WebDriverWait(driver, 15).until(wait_EC).click()

                logging.info('Aguarda a pagina com os vídeos carregar.')
                class_name = 'video-menu__item__content'
                wait_EC = EC.presence_of_all_elements_located((By.CLASS_NAME, class_name))
                videos_minutagem = WebDriverWait(driver, 15).until(wait_EC)

                for video_minutagem in videos_minutagem:
                    nome_video = video_minutagem.find_element(By.XPATH, './p')\
                        .get_attribute('innerHTML').strip()
                    tempo_video = video_minutagem.find_element(By.XPATH, './small')\
                        .get_attribute('innerHTML')

                    logging.info(
                        f'Modulo: {nome_modulo}, '\
                        f'Matéria: {nome_materia}, '\
                        f'Aula: {aula_name}, '\
                        f'Video: {nome_video}, '\
                        f'duração: {tempo_video}.'
                        )

                    output.append((
                        nome_modulo,
                        nome_materia,
                        aula_name,
                        nome_video,
                        tempo_video
                    ))

                logging.info('Aguarda a página com as aulas carregar.')
                driver.get(url_aulas)
                sleep(20)

            url_disciplinas(driver)

        return output

    sleep(2)
    all_modulos_name = get_all_modulos_name()
    all_materias_name = get_all_materias_name(all_modulos_name)
    all_aulas_tempo = get_all_aulas_tempo(all_materias_name)

    return all_aulas_tempo


def gera_csv(lista_de_tuplas):
    # Nome do arquivo CSV
    nome_arquivo_csv = 'output.csv'

    # Escrever a lista de tuplas no arquivo CSV
    with open(nome_arquivo_csv, 'w', newline='') as arquivo_csv:
        escritor_csv = csv.writer(arquivo_csv)

        # Escrever os cabeçalhos, se necessário
        escritor_csv.writerow(['Modulo', 'Matéria', 'Aula', 'Video', 'duração'])

        # Escrever os dados
        escritor_csv.writerows(lista_de_tuplas)

    logging.info(f'Gerado o CSV {nome_arquivo_csv} com a minutagem de todos os vídeosA lista de tuplas foi salva no arquivo CSV')


if __name__ == "__main__":
    driver = launch_driver()
    login(driver)
    url_disciplinas(driver)
    output = gera_minutagem(driver)
    gera_csv(output)
    logout(driver)
    close(driver)
