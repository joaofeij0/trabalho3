import glfw
from OpenGL.GL import *
import numpy as np
import math
from imgui_bundle import imgui, hello_imgui

# Como rodar?
# 1. Instale as dependências:
#   pip install glfw PyOpenGL numpy imgui-bundle

# 2. Execute o projeto:
#   python trabalho3.py

# ==========================================================
# 1. ENGINE
# ==========================================================

def matriz_identidade():
    # Retorna a matriz base 4x4 com 1s na diagonal. É o nosso ponto de partida.
    return np.identity(4, dtype=np.float32)

def matriz_translacao(x, y, z):
    # Insere as posições X, Y e Z na última linha da matriz 4x4 para mover os objetos pelo cenário.
    m = matriz_identidade()
    m[3, 0:3] = [x, y, z]
    return m

def matriz_escala(x, y, z):
    # Multiplica a diagonal principal para alterar o tamanho do objeto nos 3 eixos.
    m = matriz_identidade()
    m[0, 0], m[1, 1], m[2, 2] = x, y, z
    return m

def matriz_rotacao_y(angulo_rad):
    # Aplica seno e cosseno para girar os vértices.
    c, s = math.cos(angulo_rad), math.sin(angulo_rad)
    m = matriz_identidade()
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, -s, s, c
    return m

def matriz_perspectiva(fov, aspecto, near, far):
    # Converte o volume de visão (frustum) no espaço NDC.
    # O FOV define a abertura da câmera, o 'aspecto' evita que a imagem fique esticada
    # e o 'near/far' definem os limites do que a câmera consegue enxergar.
    f = 1.0 / math.tan(math.radians(fov) / 2.0)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspecto
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = -1.0
    m[3, 2] = (2.0 * far * near) / (near - far)
    return m

def look_at(posicao, alvo, up):
    # Esta é a nossa Matriz de View.
    # Ela monta a base ortogonal da câmera calculando os eixos X, Y e Z no mundo
    # e depois aplica a translação inversa para posicionar a cena em volta dela.
    z = (posicao - alvo); z /= np.linalg.norm(z)  # Vetor de direção (frente invertida)
    x = np.cross(up, z); x /= np.linalg.norm(x)   # Vetor para a direita
    y = np.cross(z, x)                            # Vetor para cima real
    m = matriz_identidade()
    m[0:3, 0], m[0:3, 1], m[0:3, 2] = x, y, z
    t = matriz_translacao(-posicao[0], -posicao[1], -posicao[2])
    return np.dot(t, m)

# ==========================================================
# 2. GERADORES DE OBJETOS
# Em vez de carregar arquivos .OBJ externos, resolvimos calcular as
# coordenadas e normais de cada forma diretamente dentro do código.
# ==========================================================

def gerar_cubo():
    # Montsmos os 36 vértices (12 triângulos) para fechar as 6 faces do cubo.
    v = np.array([-0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,0.5,-0.5, 0.5,0.5,-0.5, -0.5,0.5,-0.5, -0.5,-0.5,-0.5, -0.5,-0.5,0.5, 0.5,-0.5,0.5, 0.5,0.5,0.5, 0.5,0.5,0.5, -0.5,0.5,0.5, -0.5,-0.5,0.5, -0.5,0.5,0.5, -0.5,0.5,-0.5, -0.5,-0.5,-0.5, -0.5,-0.5,-0.5, -0.5,-0.5,0.5, -0.5,0.5,0.5, 0.5,0.5,0.5, 0.5,0.5,-0.5, 0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,-0.5,0.5, 0.5,0.5,0.5, -0.5,-0.5,-0.5, 0.5,-0.5,-0.5, 0.5,-0.5,0.5, 0.5,-0.5,0.5, -0.5,-0.5,0.5, -0.5,-0.5,-0.5, -0.5,0.5,-0.5, 0.5,0.5,-0.5, 0.5,0.5,0.5, 0.5,0.5,0.5, -0.5,0.5,0.5, -0.5,0.5,-0.5], dtype=np.float32)
    # Vetores para o calculo de iluminação.
    n = np.array([0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,-1, 0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1, -1,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0, 1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0, 0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0,0,-1,0, 0,1,0,0,1,0,0,1,0,0,1,0,0,1,0,0,1,0], dtype=np.float32)
    return v, n

def gerar_esfera(raio=0.5, subdivissoes=16):
    # Para a esfera, usamos coordenadas esféricas (latitude e longitude)
    # com senos e cossenos para gerar os anéis de triângulos da malha.
    v, n = [], []
    for i in range(subdivissoes):
        lat0 = math.pi * (-0.5 + float(i) / subdivissoes)
        lat1 = math.pi * (-0.5 + float(i + 1) / subdivissoes)
        for j in range(subdivissoes):
            lng0 = 2 * math.pi * float(j) / subdivissoes
            lng1 = 2 * math.pi * float(j+1) / subdivissoes
            for lt, lg in [(lat0, lng0), (lat0, lng1), (lat1, lng0), (lat0, lng1), (lat1, lng1), (lat1, lng0)]:
                x, y, z = math.cos(lt)*math.cos(lg), math.sin(lt), math.cos(lt)*math.sin(lg)
                v.extend([x*raio, y*raio, z*raio]); n.extend([x, y, z])
    return np.array(v, dtype=np.float32), np.array(n, dtype=np.float32)

def gerar_cilindro(raio=0.5, altura=1.0, lados=20):
    # O cilindro foi feito ligando retângulos em volta do centro ao longo do eixo Y.
    v, n = [], []
    for i in range(lados):
        a0, a1 = 2*math.pi*i/lados, 2*math.pi*(i+1)/lados
        x0, z0, x1, z1 = math.cos(a0)*raio, math.sin(a0)*raio, math.cos(a1)*raio, math.sin(a1)*raio
        v.extend([x0, altura/2, z0, x1, altura/2, z1, x0, -altura/2, z0])
        n.extend([x0, 0, z0, x1, 0, z1, x0, 0, z0])
        v.extend([x1, altura/2, z1, x1, -altura/2, z1, x0, -altura/2, z0])
        n.extend([x1, 0, z1, x1, 0, z1, x0, 0, z0])
    return np.array(v, dtype=np.float32), np.array(n, dtype=np.float32)

def gerar_cone(raio=0.5, altura=1.0, lados=20):
    # No cone, todos os triângulos partem de um único ponto no topo até a base circular.
    v, n = [], []
    for i in range(lados):
        a0, a1 = 2*math.pi*i/lados, 2*math.pi*(i+1)/lados
        x0, z0, x1, z1 = math.cos(a0)*raio, math.sin(a0)*raio, math.cos(a1)*raio, math.sin(a1)*raio
        v.extend([0, altura/2, 0, x0, -altura/2, z0, x1, -altura/2, z1])
        n.extend([0, 1, 0, x0, 0, z0, x1, 0, z1])
    return np.array(v, dtype=np.float32), np.array(n, dtype=np.float32)

# ==========================================================
# 3. SHADERS E CLASSES
# ==========================================================

# Vertex Shader: Aplica o pipeline completo de transformações (Model -> View -> Projection)
# e passa a posição e a normal do objeto para o fragment shader.
vertex_code = """
#version 330
layout (location = 0) in vec3 pos;      // Posição vinda do VBO 0
layout (location = 1) in vec3 norm;     // Normal vinda do VBO 1
uniform mat4 model, view, proj;        // Nossas matrizes enviadas pelo Python
out vec3 FragNorm, FragPos;

void main() {
    FragPos = vec3(model * vec4(pos, 1.0)); // Posição global no mundo
    FragNorm = mat3(transpose(inverse(model))) * norm; // Ajusta a normal se o objeto for escalado
    gl_Position = proj * view * model * vec4(pos, 1.0); // Coordenada final de tela
}"""

# Fragment Shader: Implementa a iluminação (Ambiente + Difusa - Modelo Lambertiano).
fragment_code = """
#version 330
in vec3 FragNorm, FragPos;
out vec4 color;
uniform vec3 objColor, lightPos;
uniform float luz; 

void main() {
    // Componente de luz ambiente para o objeto não ficar 100% escuro na sombra
    vec3 amb = 0.1 * vec3(1.0); 
    
    // Componente difusa: mede o ângulo entre a normal da superfície e a direção da luz
    vec3 n = normalize(FragNorm);
    vec3 lDir = normalize(lightPos - FragPos);
    float diff = max(dot(n, lDir), 0.0);
    
    // Junta tudo e multiplica pela cor original da primitiva
    color = vec4((amb + (diff * luz)) * objColor, 1.0);
}"""

class Camera:
    # Classe criada para guardar a posição, orientação e estado da câmera FPS.
    def __init__(self):
        self.pos = np.array([0.0, 1.5, 10.0], dtype=np.float32)
        self.frente = np.array([0.0, 0.0, -1.0])
        self.yaw, self.pitch = -90.0, 0.0
        self.colisao = True

    def update(self):
        # Recalcula o vetor para onde a câmera está olhando com base nos ângulos Pitch e Yaw.
        fx = math.cos(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        fy = math.sin(math.radians(self.pitch))
        fz = math.sin(math.radians(self.yaw)) * math.cos(math.radians(self.pitch))
        self.frente = np.array([fx, fy, fz])
        self.frente /= np.linalg.norm(self.frente) # Garante tamanho 1 para o vetor

class Objeto:
    # Representa qualquer forma 3D que vai ser desenhada na tela.
    # Cuida do envio dos dados para a GPU  e da renderização.
    def __init__(self, tipo, cor, pos=(0,0,0), esc=(1,1,1)):
        self.pos, self.cor, self.esc = np.array(pos, dtype=np.float32), cor, np.array(esc)
        
        # Seleciona o gerador correto de acordo com a primitiva informada
        if tipo == "cubo": v, n = gerar_cubo()
        elif tipo == "esfera": v, n = gerar_esfera()
        elif tipo == "cilindro": v, n = gerar_cilindro()
        elif tipo == "cone": v, n = gerar_cone()
        else: v, n = gerar_cubo()
        
        self.num = len(v) // 3
        
        # Configuro o VAO para guardar o estado dos ponteiros de atributos
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)
        
        # VBO 0: Posições dos vértices na GPU
        vbo = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, v.nbytes, v, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        
        # VBO 1: Normais na GPU
        nbo = glGenBuffers(1); glBindBuffer(GL_ARRAY_BUFFER, nbo)
        glBufferData(GL_ARRAY_BUFFER, n.nbytes, n, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

    def desenhar(self, prog):
        # Para desenhar, montamos a matriz Model aplicando Translação e Escala (Model = T * S)
        m = np.dot(matriz_translacao(*self.pos), matriz_escala(*self.esc))
        
        # Passa a matriz do objeto e sua cor para os uniforms do shader
        glUniformMatrix4fv(glGetUniformLocation(prog, "model"), 1, GL_FALSE, m)
        glUniform3fv(glGetUniformLocation(prog, "objColor"), 1, self.cor)
        
        # Manda o OpenGL desenhar os triângulos armazenados no VAO
        glBindVertexArray(self.vao)
        glDrawArrays(GL_TRIANGLES, 0, self.num)

# ==========================================================
# 4. LÓGICA DO PROGRAMA E EVENTOS
# ==========================================================

cam = Camera()
objs = []
shader = None
luminosidade = 1.0
params = hello_imgui.RunnerParams() # Guarda os parâmetros e estado da janela

def testar_colisao(p_nova):
    # teste de colisão simples.
    # Se a câmera chegar muito perto da posição central de um objeto, trava o movimento.
    if not cam.colisao: return p_nova
    for i in range(1, len(objs)): # Pulo o índice 0 porque ele é o chão
        dist = np.linalg.norm([p_nova[0]-objs[i].pos[0], p_nova[2]-objs[i].pos[2]])
        if dist < (objs[i].esc[0] * 0.7): 
            return cam.pos # Retorna a posição antiga se houver colisão
    return p_nova

def setup():
    # Esta função roda uma vez só ao iniciar a aplicação.
    global shader, objs
    glEnable(GL_DEPTH_TEST) # Ativo o Z-Buffer para o openGL resolver a visibilidade de superfícies
    
    # Compila os shaders e cria o Shader Program
    vs = glCreateShader(GL_VERTEX_SHADER); glShaderSource(vs, vertex_code); glCompileShader(vs)
    fs = glCreateShader(GL_FRAGMENT_SHADER); glShaderSource(fs, fragment_code); glCompileShader(fs)
    shader = glCreateProgram(); glAttachShader(shader, vs); glAttachShader(shader, fs); glLinkProgram(shader)
    
    # Instancia os 5 objetos exigidos no trabalho espalhados pela cena
    objs.append(Objeto("plano", [0.2, 0.2, 0.2], pos=(0,-1,0), esc=(20,0.1,20))) # Chão
    objs.append(Objeto("cubo", [1,0,0], pos=(-4,0,0)))                          # Vermelho
    objs.append(Objeto("esfera", [0,1,0], pos=(-1.5,0,0)))                       # Verde
    objs.append(Objeto("cilindro", [0,0,1], pos=(1.5,0,0)))                      # Azul
    objs.append(Objeto("cone", [1,1,0], pos=(4,0,0)))                          # Amarelo

def render():
    # Esta função é chamada a cada frame desenhado na tela.
    global luminosidade, params
    glUseProgram(shader)
    glClearColor(0.1, 0.1, 0.15, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT) # Limpa os buffers de cor e de profundidade
    
    # --- CONTROLES DE NAVEGAÇÃO ---
    io = imgui.get_io()
    if not io.want_capture_keyboard: # Só move a câmera se o usuário não estiver clicando na interface
        vel = 0.08
        np_pos = cam.pos.copy()
        
        # Movimentação WASD
        if imgui.is_key_down(imgui.Key.w): np_pos += cam.frente * vel
        if imgui.is_key_down(imgui.Key.s): np_pos -= cam.frente * vel
        if imgui.is_key_down(imgui.Key.a): np_pos -= np.cross(cam.frente, [0,1,0]) * vel
        if imgui.is_key_down(imgui.Key.d): np_pos += np.cross(cam.frente, [0,1,0]) * vel
        cam.pos = testar_colisao(np_pos)
        
        # Tecla R para resetar a câmera ao ponto inicial
        if imgui.is_key_pressed(imgui.Key.r): 
            cam.pos = np.array([0.0, 1.5, 10.0])
            
        # Tecla ESC para fechar o programa
        if imgui.is_key_pressed(imgui.Key.escape):
            params.app_shall_exit = True

    # Botão direito do mouse para olhar em volta
    if imgui.is_mouse_dragging(imgui.MouseButton_.right):
        cam.yaw += io.mouse_delta.x * 0.2
        cam.pitch -= io.mouse_delta.y * 0.2
        cam.update()

    # Recalcula a Projection e a View com base na nova posição/direção da câmera
    proj = matriz_perspectiva(45.0, 1280/720, 0.1, 100.0)
    view = look_at(cam.pos, cam.pos + cam.frente, [0,1,0])
    
    # Envia as matrizes atualizadas da câmera para o shader
    glUniformMatrix4fv(glGetUniformLocation(shader, "proj"), 1, GL_FALSE, proj)
    glUniformMatrix4fv(glGetUniformLocation(shader, "view"), 1, GL_FALSE, view)
    glUniform3f(glGetUniformLocation(shader, "lightPos"), 5, 5, 5) # Posição da luz no mundo
    glUniform1f(glGetUniformLocation(shader, "luz"), luminosidade)

    # Desenha cada objeto da nossa lista
    for o in objs: o.desenhar(shader)

def gui():
    # Desenho da interface gráfica em tempo real usando Dear ImGui
    global luminosidade
    imgui.begin("Trabalho 3 - Visualizador 3D")
    imgui.text(f"Posição Câmera: {cam.pos[0]:.1f}, {cam.pos[1]:.1f}, {cam.pos[2]:.1f}")
    _, luminosidade = imgui.slider_float("Luminosidade", luminosidade, 0.0, 4.0)
    _, cam.colisao = imgui.checkbox("Ativar Colisão", cam.colisao)
    imgui.end()

# Configuração e execução do loop principal através do Hello ImGui
params.callbacks.post_init = setup
params.callbacks.custom_background = render
params.callbacks.show_gui = gui
params.app_window_params.window_geometry.size = (1280, 720)
hello_imgui.run(params)