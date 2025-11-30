"""
Script para gerar ícones do PWA a partir de um ícone base ou criando ícones programaticamente.
Execute: python app_marketplace/static/app_marketplace/generate_icons.py

Requer: pip install Pillow
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_icon_from_image(base_image_path, size, output_path):
    """Cria um ícone redimensionando uma imagem base"""
    try:
        # Carrega a imagem base
        img = Image.open(base_image_path)
        
        # Converte para RGB se necessário (remove transparência/alpha)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Cria fundo branco
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Redimensiona mantendo proporção (crop central)
        img.thumbnail((size, size), Image.Resampling.LANCZOS)
        
        # Cria imagem quadrada do tamanho exato
        square_img = Image.new('RGB', (size, size), color='#0d6efd')
        
        # Centraliza a imagem redimensionada
        if img.size[0] == size and img.size[1] == size:
            square_img = img
        else:
            # Calcula posição para centralizar
            paste_x = (size - img.size[0]) // 2
            paste_y = (size - img.size[1]) // 2
            square_img.paste(img, (paste_x, paste_y))
        
        square_img.save(output_path, 'PNG', optimize=True)
        print(f'✅ Ícone criado a partir da imagem: {output_path} ({size}x{size})')
        return True
    except Exception as e:
        print(f'❌ Erro ao criar ícone a partir da imagem: {e}')
        return False

def create_icon_programmatic(size, output_path):
    """Cria um ícone programaticamente com o logo do ÉVORA"""
    # Cria uma imagem com fundo azul do tema
    img = Image.new('RGB', (size, size), color='#0d6efd')
    draw = ImageDraw.Draw(img)
    
    # Margem
    margin = size // 8
    
    # Desenha um círculo branco (representando conectividade/rede)
    circle_margin = margin * 2
    circle_size = size - (circle_margin * 2)
    draw.ellipse(
        [(circle_margin, circle_margin), (size - circle_margin, size - circle_margin)],
        outline='#ffffff',
        width=max(3, size//20)
    )
    
    # Desenha um "E" estilizado no centro
    # Ajusta o tamanho da letra baseado no tamanho do ícone
    font_size = size // 2
    try:
        # Tenta usar uma fonte do sistema
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except:
            # Fallback para fonte padrão
            font = ImageFont.load_default()
    
    # Desenha o "E" branco
    text = "E"
    # Calcula posição para centralizar
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (size - text_width) // 2 - bbox[0]
    text_y = (size - text_height) // 2 - bbox[1]
    
    draw.text((text_x, text_y), text, fill='#ffffff', font=font)
    
    # Desenha pontos de conexão (representando a rede KMN)
    point_size = max(2, size // 30)
    points = [
        (margin * 3, margin * 3),  # Top-left
        (size - margin * 3, margin * 3),  # Top-right
        (margin * 3, size - margin * 3),  # Bottom-left
        (size - margin * 3, size - margin * 3),  # Bottom-right
    ]
    for point in points:
        draw.ellipse(
            [(point[0] - point_size, point[1] - point_size),
             (point[0] + point_size, point[1] + point_size)],
            fill='#ffffff'
        )
    
    img.save(output_path, 'PNG', optimize=True)
    print(f'✅ Ícone criado programaticamente: {output_path} ({size}x{size})')

def main():
    """Gera todos os ícones necessários"""
    sizes = [72, 96, 128, 144, 152, 192, 384, 512]
    
    # Caminho do diretório de ícones
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icons_dir = os.path.join(script_dir, 'icons')
    
    # Cria o diretório se não existir
    os.makedirs(icons_dir, exist_ok=True)
    
    # Tenta usar uma imagem base se existir
    base_images = [
        os.path.join(icons_dir, 'LOGO.jpeg'),
        os.path.join(icons_dir, 'logo.png'),
        os.path.join(icons_dir, 'logo.jpg'),
        os.path.join(icons_dir, 'icon-base.png'),
        os.path.join(icons_dir, 'icon-base.jpg'),
    ]
    
    base_image_path = None
    for img_path in base_images:
        if os.path.exists(img_path):
            base_image_path = img_path
            print(f'📷 Usando imagem base: {base_image_path}')
            break
    
    icons_created = 0
    icons_failed = 0
    
    for size in sizes:
        output_path = os.path.join(icons_dir, f'icon-{size}x{size}.png')
        
        # Se temos uma imagem base, tenta usá-la
        if base_image_path:
            if create_icon_from_image(base_image_path, size, output_path):
                icons_created += 1
            else:
                # Se falhar, cria programaticamente
                create_icon_programmatic(size, output_path)
                icons_created += 1
        else:
            # Cria programaticamente
            create_icon_programmatic(size, output_path)
            icons_created += 1
    
    print(f'\n✅ {icons_created} ícones foram gerados com sucesso!')
    if base_image_path:
        print(f'📷 Baseado em: {base_image_path}')
    else:
        print('🎨 Ícones criados programaticamente (use uma imagem logo.png/jpeg na pasta icons para personalizar)')

if __name__ == '__main__':
    main()

