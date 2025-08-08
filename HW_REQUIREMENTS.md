# 🖥️ MyCoder Hardware Requirements

## 📊 Quick Reference Table

| Scénář | Velikost | RAM min/rec | CPU min | GPU | Použití |
|--------|----------|-------------|---------|-----|---------|
| **🧪 Minimum** | 1.2 GB | 4GB/8GB | 2 cores | Ne | Testing |
| **⚡ Lightweight** | 2.6 GB | 8GB/16GB | 4 cores | Volitelné | Rychlé kódování |
| **🎯 Balanced** | 4.6 GB | 16GB/32GB | 6 cores | Doporučeno | Běžný vývoj |
| **👑 Premium** | 17.7 GB | 32GB/64GB | 8 cores | Nutné (8GB+) | **Codestral** |
| **💎 Ultimate** | 36.6 GB | 64GB/128GB | 16 cores | Nutné (16GB+) | Maximum kvalita |
| **🌟 Complete** | 55 GB | 128GB/256GB | 24 cores | Nutné (24GB+) | Production |

## 🎮 GPU Requirements by Model

| Model | Velikost | Min VRAM | Doporučené GPU | Rychlost |
|-------|----------|----------|----------------|----------|
| tinyllama | 637 MB | - | CPU only | ⭐⭐⭐⭐⭐ |
| deepseek-1.3b | 750 MB | 2GB | GTX 1050 | ⭐⭐⭐⭐☆ |
| llama3.2-3b | 2 GB | 4GB | GTX 1660 | ⭐⭐⭐☆☆ |
| codellama-7b | 3.8 GB | 8GB | RTX 3070 | ⭐⭐☆☆☆ |
| **codestral-22b** | **13 GB** | **16GB** | **RTX 4090** | **⭐⭐⭐⭐⭐** |
| codestral-q8 | 23 GB | 24GB | RTX 6000 | ⭐⭐⭐⭐⭐ |

## 🚀 Hardware Recommendations

### 💻 **Laptop Developer (8-16GB RAM)**
```
Scénář: Lightweight (2.6 GB)
Modely: deepseek-coder + llama3.2-1b
GPU: Volitelné (iGPU postačí)
Výkon: Dobrý pro základní kódování
```

### 🖥️ **Desktop Developer (16-32GB RAM)**
```
Scénář: Balanced (4.6 GB)  
Modely: codellama-7b + llama3.2-3b
GPU: GTX 1660 / RTX 3060
Výkon: Výborný pro běžný vývoj
```

### 🎮 **Gaming PC (32GB+ RAM + RTX)**
```
Scénář: Premium (17.7 GB)
Modely: Codestral + Mistral  
GPU: RTX 4070/4080/4090
Výkon: Profesionální kódování
```

### 🏢 **Workstation (64GB+ RAM + Professional GPU)**
```
Scénář: Ultimate (36.6 GB)
Modely: Codestral Q4 + Q8
GPU: RTX A6000 / H100
Výkon: Maximum možné kvality
```

## ⚡ Performance Benchmarks

| Hardware | Tokens/sec | Latence | Použití |
|----------|------------|---------|---------|
| **CPU only (16 cores)** | 10-50 | Vysoká | Testing, prototyping |
| **RTX 3070 (8GB)** | 50-150 | Střední | Vývoj, coding |
| **RTX 4090 (24GB)** | 100-300 | Nízká | **Doporučeno pro Codestral** |
| **RTX 6000 Ada (48GB)** | 200-500 | Velmi nízká | Production, research |

## 🔧 Installation Commands

```bash
# Lightweight (laptop)
./docker-build.sh quick
docker run -p 11434:11434 mycoder:latest

# Premium (desktop with GPU)
./docker-build.sh full
docker-compose up

# Custom model selection
docker exec -it mycoder ollama pull codestral:22b-v0.1-q4_0
```

## 💡 Tips & Optimization

### 🎯 **For Codestral (Premium)**
- **Minimum:** 32GB RAM + RTX 4090 (24GB VRAM)
- **Optimal:** 64GB RAM + RTX 6000 (48GB VRAM)
- **Storage:** Fast NVMe SSD (20GB+ free space)
- **Network:** Fast connection for model download

### ⚡ **Performance Tips**
- Use Q4 quantization for balance (13GB vs 23GB)
- Enable GPU acceleration for 10-100x speedup
- More RAM = faster model loading
- Fast SSD = faster Docker startup

### 🔍 **Model Selection Guide**
- **Learning/Testing:** tinyllama (637MB)
- **Laptop Coding:** deepseek-1.3b (750MB)  
- **Desktop Development:** codellama-7b (3.8GB)
- **Professional Coding:** **Codestral-22b (13GB)** ← **BEST**
- **Research/Production:** All models (55GB)

## 🏆 Why Codestral?

✅ **Specialized** for programming (80+ languages)  
✅ **Superior** code quality vs CodeLlama  
✅ **Better** context understanding  
✅ **Accurate** type hints and documentation  
✅ **Advanced** debugging suggestions  
✅ **Optimized** for multi-language projects  

**Codestral = Professional developer's choice! 👑**