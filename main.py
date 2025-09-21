// Создаем реалистичные звуковые эффекты
            function createSounds() {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                
                // Реалистичный звук ракетного двигателя
                rocketSound = {
                    context: audioContext,
                    mainEngine: null,
                    turbulence: null,
                    highFreq: null,
                    gainNodes: [],
                    filterNodes: [],
                    isPlaying: false,
                    
                    start: function() {
                        if (this.isPlaying) return;
                        this.isPlaying = true;
                        
                        // Основной двигатель
                        this.mainEngine = this.context.createOscillator();
                        const mainGain = this.context.createGain();
                        const mainFilter = this.context.createBiquadFilter();
                        
                        this.mainEngine.type = "sawtooth";
                        this.mainEngine.frequency.setValueAtTime(80, this.context.currentTime);
                        
                        mainFilter.type = "lowpass";
                        mainFilter.frequency.setValueAtTime(400, this.context.currentTime);
                        mainFilter.Q.setValueAtTime(2, this.context.currentTime);
                        
                        this.mainEngine.connect(mainFilter);
                        mainFilter.connect(mainGain);
                        mainGain.connect(this.context.destination);
                        
                        mainGain.gain.setValueAtTime(0.15, this.context.currentTime);
                        this.gainNodes.push(mainGain);
                        this.filterNodes.push(mainFilter);
                        
                        // Турбулентность
                        const turbulenceBuffer = this.createNoiseBuffer(2);
                        this.turbulence = this.context.createBufferSource();
                        this.turbulence.buffer = turbulenceBuffer;
                        this.turbulence.loop = true;
                        
                        const turbulenceGain = this.context.createGain();
                        const turbulenceFilter = this.context.createBiquadFilter();
                        
                        turbulenceFilter.type = "bandpass";
                        turbulenceFilter.frequency.setValueAtTime(800, this.context.currentTime);
                        turbulenceFilter.Q.setValueAtTime(3, this.context.currentTime);
                        
                        this.turbulence.connect(turbulenceFilter);
                        turbulenceFilter.connect(turbulenceGain);
                        turbulenceGain.connect(this.context.destination);
                        
                        turbulenceGain.gain.setValueAtTime(0.08, this.context.currentTime);
                        this.gainNodes.push(turbulenceGain);
                        this.filterNodes.push(turbulenceFilter);
                        
                        // Высокочастотный свист
                        this.highFreq = this.context.createOscillator();
                        const highGain = this.context.createGain();
                        const highFilter = this.context.createBiquadFilter();
                        
                        this.highFreq.type = "sine";
                        this.highFreq.frequency.setValueAtTime(1200, this.context.currentTime);
                        
                        highFilter.type = "highpass";
                        highFilter.frequency.setValueAtTime(1000, this.context.currentTime);
                        
                        this.highFreq.connect(highFilter);
                        highFilter.connect(highGain);
                        highGain.connect(this.context.destination);
                        
                        highGain.gain.setValueAtTime(0.05, this.context.currentTime);
                        this.gainNodes.push(highGain);
                        this.filterNodes.push(highFilter);
                        
                        // Запускаем все источники
                        this.mainEngine.start();
                        this.turbulence.start();
                        this.highFreq.start();
                    },
                    
                    createNoiseBuffer: function(duration) {
                        const bufferSize = this.context.sampleRate * duration;
                        const buffer = this.context.createBuffer(1, bufferSize, this.context.sampleRate);
                        const output = buffer.getChannelData(0);
                        
                        // Розовый шум
                        let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
                        for (let i = 0; i < bufferSize; i++) {
                            const white = Math.random() * 2 - 1;
                            b0 = 0.99886 * b0 + white * 0.0555179;
                            b1 = 0.99332 * b1 + white * 0.0750759;
                            b2 = 0.96900 * b2 + white * 0.1538520;
                            b3 = 0.86650 * b3 + white * 0.3104856;
                            b4 = 0.55000 * b4 + white * 0.5329522;
                            b5 = -0.7616 * b5 - white * 0.0168980;
                            const pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
                            b6 = white * 0.115926;
                            output[i] = pink * 0.11;
                        }
                        return buffer;
                    },
                    
                    updatePitch: function(multiplier) {
                        if (!this.isPlaying) return;
                        
                        const intensityFactor = 1 + (multiplier - 1) * 0.3;
                        const frequencyFactor = 1 + (multiplier - 1) * 0.2;
                        
                        if (this.mainEngine) {
                            const newFreq = 80 * frequencyFactor;
                            this.mainEngine.frequency.setValueAtTime(newFreq, this.context.currentTime);
                        }
                        
                        if (this.highFreq) {
                            const newHighFreq = 1200 * frequencyFactor;
                            this.highFreq.frequency.setValueAtTime(newHighFreq, this.context.currentTime);
                        }
                        
                        this.gainNodes.forEach((gainNode, index) => {
                            const baseGains = [0.15, 0.08, 0.05];
                            const newGain = baseGains[index] * intensityFactor;
                            gainNode.gain.setValueAtTime(Math.min(newGain, 0.25), this.context.currentTime);
                        });
                        
                        if (this.filterNodes[0]) {
                            const newCutoff = 400 + (multiplier - 1) * 100;
                            this.filterNodes[0].frequency.setValueAtTime(newCutoff, this.context.currentTime);
                        }
                        
                        if (this.filterNodes[1]) {
                            const newBandpass = 800 + (multiplier - 1) * 200;
                            this.filterNodes[1].frequency.setValueAtTime(newBandpass, this.context.currentTime);
                        }
                    },
                    
                    stop: function() {
                        if (!this.isPlaying) return;
                        this.isPlaying = false;
                        
                        this.gainNodes.forEach(gainNode => {
                            gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.5);
                        });
                        
                        setTimeout(() => {
                            if (this.mainEngine) {
                                this.mainEngine.stop();
                                this.mainEngine = null;
                            }
                            if (this.turbulence) {
                                this.turbulence.stop();
                                this.turbulence = null;
                            }
                            if (this.highFreq) {
                                this.highFreq.stop();
                                this.highFreq = null;
                            }
                            this.gainNodes = [];
                            this.filterNodes = [];
                        }, 500);
                    }
                };
                
                // Реалистичный звук взрыва
                crashSound = {
                    context: audioContext,
                    play: function() {
                        this.playInitialBang();
                        setTimeout(() => this.playEcho(), 200);
                        setTimeout(() => this.playDebris(), 600);
                    },
                    
                    playInitialBang: function() {
                        const noiseBuffer = this.createExplosionBuffer(0.3);
                        const noiseSource = this.context.createBufferSource();
                        const noiseGain = this.context.createGain();
                        const noiseFilter = this.context.createBiquadFilter();
                        
                        noiseSource.buffer = noiseBuffer;
                        noiseFilter.type = "lowpass";
                        noiseFilter.frequency.setValueAtTime(1200, this.context.currentTime);
                        noiseFilter.Q.setValueAtTime(0.7, this.context.currentTime);
                        
                        noiseSource.connect(noiseFilter);
                        noiseFilter.connect(noiseGain);
                        noiseGain.connect(this.context.destination);
                        
                        noiseGain.gain.setValueAtTime(0.6, this.context.currentTime);
                        noiseGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.3);
                        noiseFilter.frequency.exponentialRampToValueAtTime(80, this.context.currentTime + 0.25);
                        
                        const bassOsc = this.context.createOscillator();
                        const bassGain = this.context.createGain();
                        
                        bassOsc.type = "sine";
                        bassOsc.frequency.setValueAtTime(30, this.context.currentTime);
                        bassOsc.frequency.exponentialRampToValueAtTime(5, this.context.currentTime + 0.4);
                        
                        bassOsc.connect(bassGain);
                        bassGain.connect(this.context.destination);
                        
                        bassGain.gain.setValueAtTime(0.8, this.context.currentTime);
                        bassGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.4);
                        
                        noiseSource.start();
                        bassOsc.start();
                        
                        noiseSource.stop(this.context.currentTime + 0.3);
                        bassOsc.stop(this.context.currentTime + 0.4);
                    },
                    
                    playEcho: function() {
                        const echoBuffer = this.createExplosionBuffer(0.2);
                        const echoSource = this.context.createBufferSource();
                        const echoGain = this.context.createGain();
                        const echoFilter = this.context.createBiquadFilter();
                        
                        echoSource.buffer = echoBuffer;
                        echoFilter.type = "highpass";
                        echoFilter.frequency.setValueAtTime(200, this.context.currentTime);
                        
                        echoSource.connect(echoFilter);
                        echoFilter.connect(echoGain);
                        echoGain.connect(this.context.destination);
                        
                        echoGain.gain.setValueAtTime(0.3, this.context.currentTime);
                        echoGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.2);
                        
                        echoSource.start();
                        echoSource.stop(this.context.currentTime + 0.2);
                    },
                    
                    playDebris: function() {
                        for (let i = 0; i < 3; i++) {
                            setTimeout(() => {
                                const debris = this.context.createOscillator();
                                const debrisGain = this.context.createGain();
                                const debrisFilter = this.context.createBiquadFilter();
                                
                                debris.type = "sawtooth";
                                debris.frequency.setValueAtTime(150 + Math.random() * 300, this.context.currentTime);
                                debris.frequency.exponentialRampToValueAtTime(50 + Math.random() * 100, this.context.currentTime + 0.5);
                                
                                debrisFilter.type = "bandpass";
                                debrisFilter.frequency.setValueAtTime(400 + Math.random() * 800, this.context.currentTime);
                                debrisFilter.Q.setValueAtTime(2, this.context.currentTime);
                                
                                debris.connect(debrisFilter);
                                debrisFilter.connect(debrisGain);
                                debrisGain.connect(this.context.destination);
                                
                                debrisGain.gain.setValueAtTime(0.1, this.context.currentTime);
                                debrisGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.5);
                                
                                debris.start();
                                debris.stop(this.context.currentTime + 0.5);
                            }, i * 150);
                        }
                    },
                    
                    createExplosionBuffer: function(duration) {
                        const bufferSize = this.context.sampleRate * duration;
                        const buffer = this.context.createBuffer(1, bufferSize, this.context.sampleRate);
                        const output = buffer.getChannelData(0);
                        
                        for (let i = 0; i < bufferSize; i++) {
                            const decay = 1 - (i / bufferSize);
                            const intensity = Math.pow(decay, 0.3);
                            output[i] = (Math.random() * 2 - 1) * intensity;
                        }
                        return buffer;
                    }
                };
            }
            
            function updateDisplay() {
                document.getElementById("balance").textContent = gameData.balance;
                document.getElementById("multiplier").textContent = gameData.multiplier.toFixed(2) + "x";
                document.getElementById("currentBet").textContent = gameData.currentBet || "-";
                
                if (gameData.currentBet) {
                    const potential = Math.floor(gameData.currentBet * gameData.multiplier);
                    document.getElementById("potentialWin").textContent = potential + " монет";
                }
            }
            
            function updateRocketPosition(multiplier) {
                const maxHeight = 250;
                const height = Math.min((multiplier - 1) * 80, maxHeight);
                
                rocket.style.bottom = (20 + height) + "px";
                trail.style.height = height + "px";
                
                if (rocketSound && rocketSound.isPlaying) {
                    rocketSound.updatePitch(multiplier);
                }
            }
            
            function placeBet() {
                const betAmount = parseInt(document.getElementById("betAmount").value);
                
                if (!betAmount || betAmount < 1 || gameData.balance < betAmount || gameData.gameRunning) {
                    return;
                }
                
                gameData.balance -= betAmount;
                gameData.currentBet = betAmount;
                gameData.isPlaying = true;
                
                document.getElementById("betButton").disabled = true;
                document.getElementById("cashoutButton").disabled = false;
                document.getElementById("gameStatus").textContent = "Ставка принята";
                
                updateDisplay();
            }
            
            function cashOut() {
                if (!gameData.isPlaying || !gameData.gameRunning) return;
                
                const winAmount = Math.floor(gameData.currentBet * gameData.multiplier);
                gameData.balance += winAmount;
                gameData.isPlaying = false;
                
                document.getElementById("cashoutButton").disabled = true;
                document.getElementById("gameStatus").textContent = "Выведено: " + winAmount + " монет";
                
                updateDisplay();
            }
            
            function simulateGame() {
                gameData.multiplier = 1.0;
                gameData.gameRunning = false;
                
                rocket.style.bottom = "20px";
                rocket.classList.remove("flying");
                trail.style.height = "0px";
                rocket.style.display = "block";
                explosion.style.display = "none";
                
                document.getElementById("betButton").disabled = false;
                document.getElementById("cashoutButton").disabled = true;
                document.getElementById("gameStatus").textContent = "Прием ставок...";
                
                setTimeout(function() {
                    gameData.gameRunning = true;
                    document.getElementById("betButton").disabled = true;
                    document.getElementById("gameStatus").textContent = "Игра началась!";
                    
                    if (!rocketSound) createSounds();
                    rocketSound.start();
                    rocket.classList.add("flying");
                    
                    const crashPoint = Math.random() * 3 + 1.01;
                    
                    const gameInterval = setInterval(function() {
                        gameData.multiplier += 0.01 + (gameData.multiplier * 0.001);
                        updateRocketPosition(gameData.multiplier);
                        
                        if (gameData.multiplier >= crashPoint) {
                            crash();
                            clearInterval(gameInterval);
                        }
                        
                        updateDisplay();
                    }, 100);
                    
                }, 5000);
            }
            
            function crash() {
                gameData.gameRunning = false;
                
                if (rocketSound) rocketSound.stop();
                if (crashSound) crashSound.play();
                
                rocket.classList.remove("flying");
                rocket.style.display = "none";
                explosion.style.display = "block";
                explosion.style.bottom = rocket.style.bottom;
                explosion.style.left = "50%";
                explosion.style.transform = "translateX(-50%)";
                
                const multiplierElement = document.getElementById("multiplier");
                multiplierElement.classList.add("crashed");
                multiplierElement.textContent = "КРАШ!";
                
                if (gameData.isPlaying) {
                    gameData.isPlaying = false;
                    document.getElementById("gameStatus").textContent = "Краш - проигрыш!";
                }
                
                setTimeout(function() {
                    multiplierElement.classList.remove("crashed");
                    gameData.currentBet = 0;
                    gameData.isPlaying = false;
                    updateDisplay();
                    simulateGame();
                }, 3000);
            }
            
            // Дополнительные CSS стили для crash игры
            const crashStyles = `
                .rocket {
                    position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                    font-size: 50px; transition: all 0.3s ease;
                    filter: drop-shadow(0 0 10px #ff6b35);
                }
                .rocket.flying {
                    animation: rocketFly 0.1s linear infinite;
                }
                @keyframes rocketFly {
                    0% { transform: translateX(-50%) rotate(-2deg); }
                    50% { transform: translateX(-50%) rotate(2deg); }
                    100% { transform: translateX(-50%) rotate(-2deg); }
                }
                .explosion {
                    display: none; position: absolute; font-size: 80px;
                    animation: explode 0.8s ease forwards;
                }
                @keyframes explode {
                    0% { transform: scale(0.2); opacity: 1; }
                    50% { transform: scale(1.5); opacity: 1; }
                    100% { transform: scale(2.5); opacity: 0; }
                }
                .multiplier { 
                    font-size: 48px; font-weight: bold; color: #00ff00; 
                    text-shadow: 0 0 20px #00ff00; transition: all 0.1s ease;
                    z-index: 10; position: relative;
                }
                .multiplier.crashed { color: #ff0000; text-shadow: 0 0 20px #ff0000; }
                .controls { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
                .bet-input { 
                    padding: 15px; background: rgba(255,255,255,0.1); 
                    border: 1px solid rgba(255,255,255,0.3);
                    border-radius: 15px; color: #fff; font-size: 16px; text-align: center;
                }
                .btn { 
                    padding: 15px; border: none; border-radius: 15px; font-weight: bold; 
                    font-size: 16px; cursor: pointer; transition: all 0.3s ease; text-transform: uppercase;
                }
                .btn-bet { background: linear-gradient(45deg, #00ff00, #32cd32); color: #000; }
                .btn-cashout { background: linear-gradient(45deg, #ff6b6b, #ff4757); color: #fff; }
                .btn:disabled { background: rgba(255,255,255,0.3); cursor: not-allowed; }
                .btn:hover:not(:disabled) { transform: translateY(-2px); }
                .game-info { 
                    background: rgba(255,255,255,0.1); padding: 15px; 
                    border-radius: 15px; margin-bottom: 20px; 
                }
                .trail {
                    position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%);
                    width: 4px; height: 0; background: linear-gradient(to top, #ff6b35, transparent);
                    transition: height 0.1s ease;
                }
                .cases-grid {
                    display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px;
                    margin-bottom: 20px;
                }
                .case-item {
                    background: linear-gradient(135deg, #667eea, #764ba2);
                    border-radius: 15px; padding: 20px; text-align: center;
                    cursor: pointer; transition: all 0.3s ease; position: relative;
                    overflow: hidden; border: 2px solid transparent;
                }
                .case-item:hover {
                    transform: translateY(-5px); border-color: #ffd700;
                    box-shadow: 0 10px 25px rgba(0,0,0,0.3);
                }
                .case-emoji {
                    font-size: 40px; display: block; margin-bottom: 10px;
                }
                .case-name {
                    font-weight: bold; margin-bottom: 5px; font-size: 14px;
                }
                .case-price {
                    color: #ffd700; font-weight: bold;
                }
                .case-rarity {
                    position: absolute; top: 5px; right: 5px;
                    padding: 2px 8px; border-radius: 10px; font-size: 10px;
                    font-weight: bold; text-transform: uppercase;
                }
            `;
            
            // Добавляем стили в head
            const styleSheet = document.createElement("style");
            styleSheet.textContent = crashStyles;
            document.head.appendChild(styleSheet);
            
            updateDisplay();
            simulateGame();
        </script>
    </body>
</html>'''
    return html_content                    // Запускаем все источники
                    this.mainEngine.start();
                    this.turbulence.start();
                    this.highFreq.start();
                },
                
                createNoiseBuffer: function(duration) {
                    const bufferSize = this.context.sampleRate * duration;
                    const buffer = this.context.createBuffer(1, bufferSize, this.context.sampleRate);
                    const output = buffer.getChannelData(0);
                    
                    // Создаем розовый шум (более реалистичный чем белый)
                    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;
                    for (let i = 0; i < bufferSize; i++) {
                        const white = Math.random() * 2 - 1;
                        b0 = 0.99886 * b0 + white * 0.0555179;
                        b1 = 0.99332 * b1 + white * 0.0750759;
                        b2 = 0.96900 * b2 + white * 0.1538520;
                        b3 = 0.86650 * b3 + white * 0.3104856;
                        b4 = 0.55000 * b4 + white * 0.5329522;
                        b5 = -0.7616 * b5 - white * 0.0168980;
                        const pink = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
                        b6 = white * 0.115926;
                        output[i] = pink * 0.11;
                    }
                    return buffer;
                },
                
                updatePitch: function(multiplier) {
                    if (!this.isPlaying) return;
                    
                    // Увеличиваем частоты и интенсивность с ростом множителя
                    const intensityFactor = 1 + (multiplier - 1) * 0.3;
                    const frequencyFactor = 1 + (multiplier - 1) * 0.2;
                    
                    if (this.mainEngine) {
                        const newFreq = 80 * frequencyFactor;
                        this.mainEngine.frequency.setValueAtTime(newFreq, this.context.currentTime);
                    }
                    
                    if (this.highFreq) {
                        const newHighFreq = 1200 * frequencyFactor;
                        this.highFreq.frequency.setValueAtTime(newHighFreq, this.context.currentTime);
                    }
                    
                    // Обновляем громкость
                    this.gainNodes.forEach((gainNode, index) => {
                        const baseGains = [0.15, 0.08, 0.05];
                        const newGain = baseGains[index] * intensityFactor;
                        gainNode.gain.setValueAtTime(Math.min(newGain, 0.25), this.context.currentTime);
                    });
                    
                    // Обновляем фильтры для более реалистичного звука
                    if (this.filterNodes[0]) { // main filter
                        const newCutoff = 400 + (multiplier - 1) * 100;
                        this.filterNodes[0].frequency.setValueAtTime(newCutoff, this.context.currentTime);
                    }
                    
                    if (this.filterNodes[1]) { // turbulence filter
                        const newBandpass = 800 + (multiplier - 1) * 200;
                        this.filterNodes[1].frequency.setValueAtTime(newBandpass, this.context.currentTime);
                    }
                },
                
                stop: function() {
                    if (!this.isPlaying) return;
                    this.isPlaying = false;
                    
                    // Плавное затухание
                    this.gainNodes.forEach(gainNode => {
                        gainNode.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.5);
                    });
                    
                    // Останавливаем через 0.5 секунд
                    setTimeout(() => {
                        if (this.mainEngine) {
                            this.mainEngine.stop();
                            this.mainEngine = null;
                        }
                        if (this.turbulence) {
                            this.turbulence.stop();
                            this.turbulence = null;
                        }
                        if (this.highFreq) {
                            this.highFreq.stop();
                            this.highFreq = null;
                        }
                        this.gainNodes = [];
                        this.filterNodes = [];
                    }, 500);
            };
            
            function switchTab(tab) {
                document.querySelectorAll(".nav-tab").forEach(t => t.classList.remove("active"));
                document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"));
                
                document.querySelector(`[onclick="switchTab('${tab}')"]`).classList.add("active");
                document.getElementById(tab + "-tab").classList.add("active");
                
                if (tab === "cases") {
                    generateCases();
                }
            }
            
            function generateCases() {
                const grid = document.getElementById("casesGrid");
                grid.innerHTML = "";
                
                Object.keys(cases).forEach(caseId => {
                    const caseData = cases[caseId];
                    const caseElement = document.createElement("div");
                    caseElement.className = "case-item";
                    caseElement.onclick = () => openCase(caseId);
                    
                    const rarity = getRarityFromPrice(caseData.price);
                    
                    caseElement.innerHTML = `
                        <div class="case-rarity rarity-${rarity}">${rarity}</div>
                        <div class="case-emoji">${caseData.emoji}</div>
                        <div class="case-name">${caseData.name}</div>
                        <div class="case-price">${caseData.price} монет</div>
                        <div style="font-size: 12px; color: #ccc; margin-top: 5px;">
                            ${caseData.items.length} подарков внутри
                        </div>
                    `;
                    
                    grid.appendChild(caseElement);
                });
            }
            
            function getRarityFromPrice(price) {
                if (price <= 150) return "common";
                if (price <= 300) return "uncommon"; 
                if (price <= 600) return "rare";
                if (price <= 900) return "epic";
                return "legendary";
            }
            
            function getRarityFromStars(stars) {
                if (stars <= 25) return "common";
                if (stars <= 100) return "uncommon";
                if (stars <= 500) return "rare";
                if (stars <= 1000) return "epic";
                if (stars <= 2000) return "legendary";
                return "mythic";
            }
            
            function openCase(caseId) {
                const caseData = cases[caseId];
                
                if (gameData.balance < caseData.price) {
                    alert("Недостаточно монет!");
                    return;
                }
                
                gameData.balance -= caseData.price;
                updateDisplay();
                
                // Создаем анимацию прокрутки подарков
                showCaseSpinner(caseData);
            }
            
            function showCaseSpinner(caseData) {
                const spinner = document.getElementById("caseSpinner");
                const track = document.getElementById("spinnerTrack");
                const status = document.getElementById("spinnerStatus");
                
                // Определяем выигрышный подарок
                const winnerGift = getRandomItem(caseData.items);
                
                // Создаем массив подарков для прокрутки (50 подарков)
                const spinnerGifts = [];
                
                // Добавляем 40 случайных подарков
                for (let i = 0; i < 40; i++) {
                    const randomGift = getRandomItem(caseData.items);
                    const giftData = realTelegramGifts[randomGift.id];
                    spinnerGifts.push({
                        ...giftData,
                        rarity: getRarityFromStars(giftData.stars)
                    });
                }
                
                // Вставляем выигрышный подарок в позицию 35 (будет по центру после анимации)
                const winnerGiftData = realTelegramGifts[winnerGift.id];
                spinnerGifts[35] = {
                    ...winnerGiftData,
                    rarity: getRarityFromStars(winnerGiftData.stars),
                    isWinner: true
                };
                
                // Добавляем еще 10 подарков в конец
                for (let i = 0; i < 10; i++) {
                    const randomGift = getRandomItem(caseData.items);
                    const giftData = realTelegramGifts[randomGift.id];
                    spinnerGifts.push({
                        ...giftData,
                        rarity: getRarityFromStars(giftData.stars)
                    });
                }
                
                // Очищаем трек и добавляем подарки
                track.innerHTML = '';
                track.style.transform = 'translateX(0px)';
                
                spinnerGifts.forEach((gift, index) => {
                    const item = document.createElement('div');
                    item.className = `spinner-item rarity-${gift.rarity}`;
                    
                    item.innerHTML = `
                        <div class="spinner-item-emoji">${gift.emoji}</div>
                        <div class="spinner-item-name">${gift.name.split(' ').slice(-1)[0]}</div>
                        <div class="spinner-item-stars">★ ${gift.stars}</div>
                    `;
                    
                    track.appendChild(item);
                });
                
                spinner.style.display = 'flex';
                status.textContent = 'Крутим кейс...';
                
                // Звук начала прокрутки
                playSpinSound();
                
                // Запускаем анимацию через небольшую задержку
                setTimeout(() => {
                    // Рассчитываем финальную позицию (выигрышный подарок в центре)
                    const itemWidth = 120; // 100px ширина + 20px отступы
                    const centerOffset = 175; // Половина ширины контейнера
                    const targetPosition = -(35 * itemWidth - centerOffset);
                    
                    track.style.transform = `translateX(${targetPosition}px)`;
                    
                    // Через 3 секунды показываем результат
                    setTimeout(() => {
                        const winnerItem = track.children[35];
                        winnerItem.classList.add('winner');
                        
                        status.textContent = 'Поздравляем!';
                        
                        // Звук выигрыша
                        setTimeout(() => {
                            playWinSound(winnerGiftData.rarity);
                        }, 300);
                        
                        // Добавляем в инвентарь
                        gameData.inventory.push(winnerGiftData);
                        gameData.casesOpened++;
                        
                        // Показываем кнопки
                        setTimeout(() => {
                            const buttons = document.getElementById("caseOpeningButtons");
                            buttons.style.display = 'flex';
                        }, 1000);
                        
                    }, 3000);
                    
                }, 500);
            }
            
            function getRandomItem(items) {
                const totalChance = items.reduce((sum, item) => sum + item.chance, 0);
                const random = Math.random() * totalChance;
                
                let currentChance = 0;
                for (const item of items) {
                    currentChance += item.chance;
                    if (random <= currentChance) {
                        return item;
                    }
                }
                return items[0];
            }
            
            function closeCaseSpinner() {
                const spinner = document.getElementById("caseSpinner");
                spinner.style.display = 'none';
                
                const buttons = document.getElementById("caseOpeningButtons");
                buttons.style.display = 'none';
                
                // Обновляем статистику
                updateCaseStats();
            }
            
            function updateCaseStats() {
                document.getElementById("inventoryCount").textContent = gameData.inventory.length;
                document.getElementById("casesOpened").textContent = gameData.casesOpened;
                
                const totalStars = gameData.inventory.reduce((sum, item) => sum + item.stars, 0);
                document.getElementById("inventoryValue").textContent = totalStars;
            }
            
            function openAnotherCase() {
                closeCaseSpinner();
                // Возвращаемся к выбору кейсов
                switchTab('cases');
            }
            
            function playSpinSound() {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                
                // Создаем звук прокрутки - быстрые клики
                let clickCount = 0;
                const clickInterval = setInterval(() => {
                    if (clickCount > 30) {
                        clearInterval(clickInterval);
                        return;
                    }
                    
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();
                    
                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);
                    
                    oscillator.frequency.setValueAtTime(800 + clickCount * 10, audioContext.currentTime);
                    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
                    
                    oscillator.start();
                    oscillator.stop(audioContext.currentTime + 0.1);
                    
                    clickCount++;
                }, 100);
            }
            
            function playWinSound(rarity) {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                let frequencies = [523, 659, 784];
                
                switch(rarity) {
                    case "uncommon": frequencies = [523, 659, 784]; break;
                    case "rare": frequencies = [659, 784, 988]; break;
                    case "epic": frequencies = [784, 988, 1175]; break;
                    case "legendary": frequencies = [988, 1175, 1397]; break;
                    case "mythic": 
                        frequencies = [1175, 1397, 1661, 1975]; 
                        // Дополнительные эффекты для мифических
                        setTimeout(() => playFireworks(), 200);
                        break;
                }
                
                frequencies.forEach((freq, i) => {
                    setTimeout(() => {
                        const oscillator = audioContext.createOscillator();
                        const gainNode = audioContext.createGain();
                        
                        oscillator.connect(gainNode);
                        gainNode.connect(audioContext.destination);
                        
                        oscillator.frequency.setValueAtTime(freq, audioContext.currentTime);
                        gainNode.gain.setValueAtTime(0.15, audioContext.currentTime);
                        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.6);
                        
                        oscillator.start();
                        oscillator.stop(audioContext.currentTime + 0.6);
                    }, i * 150);
                });
            }
            
            function playFireworks() {
                // Звук фейерверка для мифических предметов
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                
                for (let i = 0; i < 5; i++) {
                    setTimeout(() => {
                        const oscillator = audioContext.createOscillator();
                        const gainNode = audioContext.createGain();
                        const filterNode = audioContext.createBiquadFilter();
                        
                        oscillator.connect(filterNode);
                        filterNode.connect(gainNode);
                        gainNode.connect(audioContext.destination);
                        
                        oscillator.type = "sawtooth";
                        oscillator.frequency.setValueAtTime(200 + Math.random() * 800, audioContext.currentTime);
                        
                        filterNode.type = "bandpass";
                        filterNode.frequency.setValueAtTime(1000 + Math.random() * 2000, audioContext.currentTime);
                        
                        gainNode.gain.setValueAtTime(0.2, audioContext.currentTime);
                        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.8);
                        
                        oscillator.start();
                        oscillator.stop(audioContext.currentTime + 0.8);
                    }, i * 200);
                }
            }
            
            // Более реалистичный звук взрыва с несколькими фазами
            crashSound = {
                context: audioContext,
                play: function() {
                    // Фаза 1: Начальный взрыв
                    this.playInitialBang();
                    
                    // Фаза 2: Эхо и реверберация (через 200мс)
                    setTimeout(() => this.playEcho(), 200);
                    
                    // Фаза 3: Затухающие обломки (через 600мс)
                    setTimeout(() => this.playDebris(), 600);
                },
                
                playInitialBang: function() {
                    // Создаем импульсивный взрыв
                    const noiseBuffer = this.createExplosionBuffer(0.3);
                    const noiseSource = this.context.createBufferSource();
                    const noiseGain = this.context.createGain();
                    const noiseFilter = this.context.createBiquadFilter();
                    
                    noiseSource.buffer = noiseBuffer;
                    noiseFilter.type = "lowpass";
                    noiseFilter.frequency.setValueAtTime(1200, this.context.currentTime);
                    noiseFilter.Q.setValueAtTime(0.7, this.context.currentTime);
                    
                    noiseSource.connect(noiseFilter);
                    noiseFilter.connect(noiseGain);
                    noiseGain.connect(this.context.destination);
                    
                    noiseGain.gain.setValueAtTime(0.6, this.context.currentTime);
                    noiseGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.3);
                    noiseFilter.frequency.exponentialRampToValueAtTime(80, this.context.currentTime + 0.25);
                    
                    // Низкочастотный удар
                    const bassOsc = this.context.createOscillator();
                    const bassGain = this.context.createGain();
                    
                    bassOsc.type = "sine";
                    bassOsc.frequency.setValueAtTime(30, this.context.currentTime);
                    bassOsc.frequency.exponentialRampToValueAtTime(5, this.context.currentTime + 0.4);
                    
                    bassOsc.connect(bassGain);
                    bassGain.connect(this.context.destination);
                    
                    bassGain.gain.setValueAtTime(0.8, this.context.currentTime);
                    bassGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.4);
                    
                    noiseSource.start();
                    bassOsc.start();
                    
                    noiseSource.stop(this.context.currentTime + 0.3);
                    bassOsc.stop(this.context.currentTime + 0.4);
                },
                
                playEcho: function() {
                    // Эхо взрыва
                    const echoBuffer = this.createExplosionBuffer(0.2);
                    const echoSource = this.context.createBufferSource();
                    const echoGain = this.context.createGain();
                    const echoFilter = this.context.createBiquadFilter();
                    
                    echoSource.buffer = echoBuffer;
                    echoFilter.type = "highpass";
                    echoFilter.frequency.setValueAtTime(200, this.context.currentTime);
                    
                    echoSource.connect(echoFilter);
                    echoFilter.connect(echoGain);
                    echoGain.connect(this.context.destination);
                    
                    echoGain.gain.setValueAtTime(0.3, this.context.currentTime);
                    echoGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.2);
                    
                    echoSource.start();
                    echoSource.stop(this.context.currentTime + 0.2);
                },
                
                playDebris: function() {
                    // Звук падающих обломков
                    for (let i = 0; i < 3; i++) {
                        setTimeout(() => {
                            const debris = this.context.createOscillator();
                            const debrisGain = this.context.createGain();
                            const debrisFilter = this.context.createBiquadFilter();
                            
                            debris.type = "sawtooth";
                            debris.frequency.setValueAtTime(150 + Math.random() * 300, this.context.currentTime);
                            debris.frequency.exponentialRampToValueAtTime(50 + Math.random() * 100, this.context.currentTime + 0.5);
                            
                            debrisFilter.type = "bandpass";
                            debrisFilter.frequency.setValueAtTime(400 + Math.random() * 800, this.context.currentTime);
                            debrisFilter.Q.setValueAtTime(2, this.context.currentTime);
                            
                            debris.connect(debrisFilter);
                            debrisFilter.connect(debrisGain);
                            debrisGain.connect(this.context.destination);
                            
                            debrisGain.gain.setValueAtTime(0.1, this.context.currentTime);
                            debrisGain.gain.exponentialRampToValueAtTime(0.001, this.context.currentTime + 0.5);
                            
                            debris.start();
                            debris.stop(this.context.currentTime + 0.5);
                        }, i * 150);
                    }
                },
                
                createExplosionBuffer: function(duration) {
                    const bufferSize = this.context.sampleRate * duration;
                    const buffer = this.context.createBuffer(1, bufferSize, this.context.sampleRate);
                    const output = buffer.getChannelData(0);
                    
                    // Создаем шум взрыва с затуханием
                    for (let i = 0; i < bufferSize; i++) {
                        const decay = 1 - (i / bufferSize);
                        const intensity = Math.pow(decay, 0.3);
                        output[i] = (Math.random() * 2 - 1) * intensity;
                    }
                    return buffer;
                }
            };
        }import os
import requests
import json
import random
import time
import threading
from flask import Flask, request, jsonify
import logging
from datetime import datetime, timedelta

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Настройки
TOKEN = os.environ.get('BOT_TOKEN')
WEBHOOK_URL = "https://lambo-gift-bot.onrender.com"

if not TOKEN:
    raise ValueError("BOT_TOKEN environment variable is required")

API_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

# Глобальные переменные для игры
users = {}
current_crash_game = None
game_lock = threading.Lock()

# Обновленная система подарков на основе реальных Telegram Gifts
REAL_TELEGRAM_GIFTS = {
    # Hanging Star (самые дорогие)
    "hanging_star_1649": {"name": "💫 Hanging Star", "stars": 1649, "emoji": "💫", "rarity": "mythic"},
    "hanging_star_1554": {"name": "💫 Hanging Star", "stars": 1554, "emoji": "💫", "rarity": "mythic"},
    "hanging_star_1545": {"name": "💫 Hanging Star", "stars": 1545, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1500": {"name": "💫 Hanging Star", "stars": 1500, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1499": {"name": "💫 Hanging Star", "stars": 1499, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1443": {"name": "💫 Hanging Star", "stars": 1443, "emoji": "💫", "rarity": "legendary"},
    "hanging_star_1422": {"name": "💫 Hanging Star", "stars": 1422, "emoji": "💫", "rarity": "epic"},
    
    # Mad Pumpkin (дорогие хэллоуин подарки)
    "mad_pumpkin_5151": {"name": "🎃 Mad Pumpkin", "stars": 5151, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_5125": {"name": "🎃 Mad Pumpkin", "stars": 5125, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_5043": {"name": "🎃 Mad Pumpkin", "stars": 5043, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4945": {"name": "🎃 Mad Pumpkin", "stars": 4945, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4739": {"name": "🎃 Mad Pumpkin", "stars": 4739, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4533": {"name": "🎃 Mad Pumpkin", "stars": 4533, "emoji": "🎃", "rarity": "mythic"},
    "mad_pumpkin_4431": {"name": "🎃 Mad Pumpkin", "stars": 4431, "emoji": "🎃", "rarity": "mythic"},
    
    # Evil Eye (средне-дорогие)
    "evil_eye_979": {"name": "👁 Evil Eye", "stars": 979, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_969": {"name": "👁 Evil Eye", "stars": 969, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_967": {"name": "👁 Evil Eye", "stars": 967, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_960": {"name": "👁 Evil Eye", "stars": 960, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_948": {"name": "👁 Evil Eye", "stars": 948, "emoji": "👁", "rarity": "legendary"},
    "evil_eye_946": {"name": "👁 Evil Eye", "stars": 946, "emoji": "👁", "rarity": "epic"},
    "evil_eye_897": {"name": "👁 Evil Eye", "stars": 897, "emoji": "👁", "rarity": "epic"},
    "evil_eye_892": {"name": "👁 Evil Eye", "stars": 892, "emoji": "👁", "rarity": "epic"},
    "evil_eye_886": {"name": "👁 Evil Eye", "stars": 886, "emoji": "👁", "rarity": "epic"},
    "evil_eye_874": {"name": "👁 Evil Eye", "stars": 874, "emoji": "👁", "rarity": "epic"},
    
    # Jelly Bunny (средние)
    "jelly_bunny_925": {"name": "🐰 Jelly Bunny", "stars": 925, "emoji": "🐰", "rarity": "legendary"},
    "jelly_bunny_923": {"name": "🐰 Jelly Bunny", "stars": 923, "emoji": "🐰", "rarity": "legendary"},
    "jelly_bunny_921": {"name": "🐰 Jelly Bunny", "stars": 921, "emoji": "🐰", "rarity": "legendary"},
    "jelly_bunny_905": {"name": "🐰 Jelly Bunny", "stars": 905, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_900": {"name": "🐰 Jelly Bunny", "stars": 900, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_894": {"name": "🐰 Jelly Bunny", "stars": 894, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_867": {"name": "🐰 Jelly Bunny", "stars": 867, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_865": {"name": "🐰 Jelly Bunny", "stars": 865, "emoji": "🐰", "rarity": "epic"},
    "jelly_bunny_824": {"name": "🐰 Jelly Bunny", "stars": 824, "emoji": "🐰", "rarity": "rare"},
    "jelly_bunny_818": {"name": "🐰 Jelly Bunny", "stars": 818, "emoji": "🐰", "rarity": "rare"},
    "jelly_bunny_816": {"name": "🐰 Jelly Bunny", "stars": 816, "emoji": "🐰", "rarity": "rare"},
    
    # B-Day Candle (дешевые)
    "bday_candle_334": {"name": "🕯 B-Day Candle", "stars": 334, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_319": {"name": "🕯 B-Day Candle", "stars": 319, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_317": {"name": "🕯 B-Day Candle", "stars": 317, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_309": {"name": "🕯 B-Day Candle", "stars": 309, "emoji": "🕯", "rarity": "uncommon"},
    "bday_candle_307": {"name": "🕯 B-Day Candle", "stars": 307, "emoji": "🕯", "rarity": "common"},
    
    # Desk Calendar (средне-дешевые)
    "desk_calendar_301": {"name": "📅 Desk Calendar", "stars": 301, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_299": {"name": "📅 Desk Calendar", "stars": 299, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_295": {"name": "📅 Desk Calendar", "stars": 295, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_289": {"name": "📅 Desk Calendar", "stars": 289, "emoji": "📅", "rarity": "uncommon"},
    "desk_calendar_287": {"name": "📅 Desk Calendar", "stars": 287, "emoji": "📅", "rarity": "common"},
    "desk_calendar_199": {"name": "📅 Desk Calendar", "stars": 199, "emoji": "📅", "rarity": "common"},
    
    # Базовые дешевые подарки
    "delicious_cake": {"name": "🎂 Delicious Cake", "stars": 1, "emoji": "🎂", "rarity": "common"},
    "green_star": {"name": "💚 Green Star", "stars": 2, "emoji": "💚", "rarity": "common"},
    "fireworks": {"name": "🎆 Fireworks", "stars": 5, "emoji": "🎆", "rarity": "common"},
    "blue_star": {"name": "💙 Blue Star", "stars": 10, "emoji": "💙", "rarity": "common"},
    "red_heart": {"name": "❤️ Red Heart", "stars": 25, "emoji": "❤️", "rarity": "uncommon"},
}

# Кейсы с реалистичными подарками и шансами
CASES = {
    "basic_gifts": {
        "name": "Базовые Подарки", 
        "emoji": "🎁", 
        "price": 50,
        "items": [
            {"id": "delicious_cake", "chance": 35},
            {"id": "green_star", "chance": 30},
            {"id": "fireworks", "chance": 20},
            {"id": "blue_star", "chance": 12},
            {"id": "red_heart", "chance": 3}
        ]
    },
    "calendar_case": {
        "name": "Календарные Подарки", 
        "emoji": "📅", 
        "price": 150,
        "items": [
            {"id": "desk_calendar_199", "chance": 25},
            {"id": "desk_calendar_287", "chance": 20},
            {"id": "desk_calendar_289", "chance": 18},
            {"id": "desk_calendar_295", "chance": 15},
            {"id": "desk_calendar_299", "chance": 12},
            {"id": "desk_calendar_301", "chance": 10}
        ]
    },
    "birthday_case": {
        "name": "День Рождения", 
        "emoji": "🕯", 
        "price": 200,
        "items": [
            {"id": "bday_candle_307", "chance": 25},
            {"id": "bday_candle_309", "chance": 20},
            {"id": "bday_candle_317", "chance": 18},
            {"id": "bday_candle_319", "chance": 15},
            {"id": "bday_candle_334", "chance": 12},
            {"id": "red_heart", "chance": 10}
        ]
    },
    "bunny_case": {
        "name": "Желейные Кролики", 
        "emoji": "🐰", 
        "price": 500,
        "items": [
            {"id": "jelly_bunny_816", "chance": 20},
            {"id": "jelly_bunny_818", "chance": 18},
            {"id": "jelly_bunny_824", "chance": 16},
            {"id": "jelly_bunny_865", "chance": 14},
            {"id": "jelly_bunny_867", "chance": 12},
            {"id": "jelly_bunny_894", "chance": 8},
            {"id": "jelly_bunny_900", "chance": 6},
            {"id": "jelly_bunny_905", "chance": 4},
            {"id": "jelly_bunny_921", "chance": 2}
        ]
    },
    "evil_eye_case": {
        "name": "Дурной Глаз", 
        "emoji": "👁", 
        "price": 750,
        "items": [
            {"id": "evil_eye_874", "chance": 20},
            {"id": "evil_eye_886", "chance": 18},
            {"id": "evil_eye_892", "chance": 16},
            {"id": "evil_eye_897", "chance": 14},
            {"id": "evil_eye_946", "chance": 12},
            {"id": "evil_eye_948", "chance": 8},
            {"id": "evil_eye_960", "chance": 6},
            {"id": "evil_eye_967", "chance": 4},
            {"id": "evil_eye_969", "chance": 1.5},
            {"id": "evil_eye_979", "chance": 0.5}
        ]
    },
    "hanging_star_case": {
        "name": "Висящие Звезды", 
        "emoji": "💫", 
        "price": 1000,
        "items": [
            {"id": "hanging_star_1422", "chance": 25},
            {"id": "hanging_star_1443", "chance": 20},
            {"id": "hanging_star_1499", "chance": 15},
            {"id": "hanging_star_1500", "chance": 12},
            {"id": "hanging_star_1545", "chance": 10},
            {"id": "hanging_star_1554", "chance": 8},
            {"id": "hanging_star_1649", "chance": 5},
            {"id": "evil_eye_979", "chance": 5}
        ]
    },
    "ultimate_pumpkin_case": {
        "name": "Безумные Тыквы", 
        "emoji": "🎃", 
        "price": 2000,
        "items": [
            {"id": "mad_pumpkin_4431", "chance": 20},
            {"id": "mad_pumpkin_4533", "chance": 18},
            {"id": "mad_pumpkin_4739", "chance": 15},
            {"id": "mad_pumpkin_4945", "chance": 12},
            {"id": "mad_pumpkin_5043", "chance": 10},
            {"id": "mad_pumpkin_5125", "chance": 8},
            {"id": "mad_pumpkin_5151", "chance": 5},
            {"id": "hanging_star_1649", "chance": 7},
            {"id": "evil_eye_979", "chance": 5}
        ]
    }
}

class CrashGame:
    def __init__(self):
        self.multiplier = 1.0
        self.is_running = False
        self.is_crashed = False
        self.bets = {}
        self.cashed_out = {}
        self.start_time = None
        self.crash_point = None
        
    def start_round(self):
        self.multiplier = 1.0
        self.is_running = True
        self.is_crashed = False
        self.bets = {}
        self.cashed_out = {}
        self.start_time = time.time()
        self.crash_point = self.generate_crash_point()
        logger.info(f"New crash game started. Crash point: {self.crash_point:.2f}")
        
    def generate_crash_point(self):
        rand = random.random()
        if rand < 0.05:
            return random.uniform(10.0, 100.0)
        elif rand < 0.15:
            return random.uniform(5.0, 10.0)
        elif rand < 0.35:
            return random.uniform(2.0, 5.0)
        else:
            return random.uniform(1.01, 2.0)
    
    def update_multiplier(self):
        if not self.is_running or self.is_crashed:
            return
            
        elapsed = time.time() - self.start_time
        self.multiplier = 1.0 + elapsed * 0.1 * (1 + elapsed * 0.05)
        
        if self.multiplier >= self.crash_point:
            self.crash()
    
    def crash(self):
        self.is_crashed = True
        self.is_running = False
        logger.info(f"Game crashed at {self.multiplier:.2f}")
        
        # Обработка проигравших ставок
        for user_id in self.bets:
            if user_id not in self.cashed_out:
                user_data = get_user_data(user_id)
                user_data['total_lost'] += self.bets[user_id]['amount']
                user_data['games_lost'] += 1
    
    def place_bet(self, user_id, amount, auto_cashout=None):
        user_id_str = str(user_id)
        
        if self.is_running:
            return False, "Игра уже идет"
        
        user_data = get_user_data(user_id)
        if user_data['balance'] < amount:
            return False, "Недостаточно средств"
        
        user_data['balance'] -= amount
        user_data['total_bet'] += amount
        user_data['games_played'] += 1
        
        self.bets[user_id_str] = {
            'amount': amount,
            'auto_cashout': auto_cashout
        }
        return True, "Ставка принята"
    
    def cashout(self, user_id):
        user_id_str = str(user_id)
        
        if not self.is_running or self.is_crashed:
            return False, "Игра не идет"
        
        if user_id_str not in self.bets:
            return False, "У вас нет ставки"
        
        if user_id_str in self.cashed_out:
            return False, "Вы уже вывели"
        
        bet_amount = self.bets[user_id_str]['amount']
        win_amount = int(bet_amount * self.multiplier)
        
        user_data = get_user_data(user_id)
        user_data['balance'] += win_amount
        user_data['total_won'] += win_amount
        user_data['games_won'] += 1
        
        self.cashed_out[user_id_str] = self.multiplier
        return True, f"Выведено {win_amount} монет при x{self.multiplier:.2f}"

def get_user_data(user_id):
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {
            "balance": 1000,
            "gifts_sent": 0,
            "gifts_received": 0,
            "total_spent": 0,
            "games_played": 0,
            "games_won": 0,
            "games_lost": 0,
            "total_bet": 0,
            "total_won": 0,
            "total_lost": 0,
            "last_bonus": None,
            "level": 1,
            "experience": 0,
            "achievements": [],
            "inventory": {},
            "referrals": [],
            "cases_opened": 0
        }
    return users[user_id]

def send_message(chat_id, text, reply_markup=None):
    try:
        url = f"{API_URL}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if not result.get("ok"):
            logger.error(f"Send message error: {result}")
            
        return result
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return None

def edit_message(chat_id, message_id, text, reply_markup=None):
    try:
        url = f"{API_URL}/editMessageText"
        data = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }
        if reply_markup:
            data["reply_markup"] = json.dumps(reply_markup)
        
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        
        if not result.get("ok"):
            logger.error(f"Edit message error: {result}")
            
        return result
    except Exception as e:
        logger.error(f"Failed to edit message: {e}")
        return None

def answer_callback(callback_query_id, text=""):
    try:
        url = f"{API_URL}/answerCallbackQuery"
        data = {
            "callback_query_id": callback_query_id,
            "text": text
        }
        response = requests.post(url, data=data, timeout=5)
        return response.json()
    except Exception as e:
        logger.error(f"Failed to answer callback: {e}")
        return None

def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚀 Играть в Crash", "callback_data": "play_crash"}],
            [{"text": "🎁 Магазин подарков", "callback_data": "gift_shop"}],
            [{"text": "💰 Баланс", "callback_data": "balance"}, {"text": "📊 Статистика", "callback_data": "stats"}],
            [{"text": "🎁 Ежедневный бонус", "callback_data": "daily_bonus"}],
            [{"text": "🏆 Достижения", "callback_data": "achievements"}, {"text": "👥 Рефералы", "callback_data": "referrals"}],
            [{"text": "🎮 WebApp", "web_app": {"url": f"{WEBHOOK_URL}/webapp"}}]
        ]
    }

def handle_start(chat_id, user_name, referrer_id=None):
    user_data = get_user_data(chat_id)
    
    # Обработка реферальной системы
    if referrer_id and str(referrer_id) != str(chat_id):
        referrer_data = get_user_data(referrer_id)
        if str(chat_id) not in referrer_data['referrals']:
            referrer_data['balance'] += 500
            referrer_data['referrals'].append(str(chat_id))
            user_data['balance'] += 200
            
            send_message(referrer_id, f"🎉 Новый реферал! +500 монет\nВсего рефералов: {len(referrer_data['referrals'])}")
    
    text = f"""🎁 <b>Добро пожаловать в GiftBot, {user_name}!</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} ({user_data['experience']} XP)

🚀 <b>Crash Game</b> - главная игра!
🎁 <b>Магазин подарков</b> - купите подарки друзьям
📈 <b>Статистика</b> - ваши достижения

💡 <i>Совет: начните с малых ставок!</i>"""

    send_message(chat_id, text, main_menu_keyboard())

def handle_crash_game(chat_id, message_id):
    global current_crash_game
    
    user_data = get_user_data(chat_id)
    
    if current_crash_game and current_crash_game.is_running:
        game_status = f"🚀 Игра идет! x{current_crash_game.multiplier:.2f}"
        if str(chat_id) in current_crash_game.bets:
            bet_info = current_crash_game.bets[str(chat_id)]
            game_status += f"\n💰 Ваша ставка: {bet_info['amount']} монет"
            if str(chat_id) in current_crash_game.cashed_out:
                game_status += f"\n✅ Выведено при x{current_crash_game.cashed_out[str(chat_id)]:.2f}"
    elif current_crash_game and current_crash_game.is_crashed:
        game_status = f"💥 Краш при x{current_crash_game.multiplier:.2f}!\nСледующая игра через 10 секунд..."
    else:
        game_status = "⏳ Ожидание начала игры..."
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎯 Ставка 10", "callback_data": "bet_10"}, {"text": "🎯 Ставка 50", "callback_data": "bet_50"}],
            [{"text": "🎯 Ставка 100", "callback_data": "bet_100"}, {"text": "🎯 Ставка 500", "callback_data": "bet_500"}],
            [{"text": "💸 Вывести", "callback_data": "cashout"}],
            [{"text": "📈 История игр", "callback_data": "game_history"}],
            [{"text": "🔙 Назад", "callback_data": "main"}]
        ]
    }
    
    text = f"""🚀 <b>Crash Game</b>

💰 <b>Ваш баланс:</b> {user_data['balance']} монет

🎮 <b>Статус игры:</b>
{game_status}

📊 <b>Ваша статистика:</b>
• Игр сыграно: {user_data['games_played']}
• Побед: {user_data['games_won']}
• Поражений: {user_data['games_lost']}
• Выиграно: {user_data['total_won']} монет

❓ <b>Как играть:</b>
1. Сделайте ставку до начала раунда
2. Следите за растущим множителем
3. Выведите до краша!"""

    edit_message(chat_id, message_id, text, keyboard)

def handle_bet(chat_id, message_id, amount):
    global current_crash_game
    
    if not current_crash_game or current_crash_game.is_running:
        return
    
    success, message = current_crash_game.place_bet(chat_id, amount)
    
    if success:
        handle_crash_game(chat_id, message_id)

def handle_cashout(chat_id, callback_query_id):
    global current_crash_game
    
    if not current_crash_game:
        answer_callback(callback_query_id, "Игра не идет")
        return
    
    success, message = current_crash_game.cashout(chat_id)
    answer_callback(callback_query_id, message)

def handle_gift_shop(chat_id, message_id):
    keyboard = {"inline_keyboard": []}
    
    for case_id, case_info in CASES.items():
        keyboard["inline_keyboard"].append([{
            "text": f"{case_info['emoji']} {case_info['name']} - {case_info['price']} монет",
            "callback_data": f"open_{case_id}"
        }])
    
    keyboard["inline_keyboard"].append([{"text": "🔙 Назад", "callback_data": "main"}])
    
    text = f"""🎁 <b>Магазин подарков</b>

Выберите кейс для открытия:

💡 <b>Как работает:</b>
• Каждый кейс содержит разные подарки
• Чем дороже подарок, тем меньше шанс его получить
• Подарки оцениваются в звездах ⭐
• Собирайте редкие подарки!

🎯 <b>Типы редкости:</b>
• ⚪ Обычные (1-25 ⭐)
• 🟢 Необычные (26-100 ⭐) 
• 🔵 Редкие (101-500 ⭐)
• 🟣 Эпические (501-1000 ⭐)
• 🟡 Легендарные (1001-2000 ⭐)
• 🔴 Мифические (2000+ ⭐)"""

    edit_message(chat_id, message_id, text, keyboard)

def open_case(chat_id, message_id, case_id):
    user_data = get_user_data(chat_id)
    case = CASES.get(case_id)
    
    if not case:
        return
    
    if user_data['balance'] < case['price']:
        keyboard = {
            "inline_keyboard": [
                [{"text": "💰 Получить бонус", "callback_data": "daily_bonus"}],
                [{"text": "🔙 К кейсам", "callback_data": "gift_shop"}]
            ]
        }
        text = f"""❌ <b>Недостаточно средств!</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
💸 <b>Нужно:</b> {case['price']} монет

{case['emoji']} <b>{case['name']}</b>"""
        edit_message(chat_id, message_id, text, keyboard)
        return
    
    # Покупаем кейс
    user_data['balance'] -= case['price']
    user_data['cases_opened'] += 1
    
    # Определяем выигрышный подарок
    winner_item_data = get_random_item_from_case(case)
    gift_data = REAL_TELEGRAM_GIFTS[winner_item_data['id']]
    
    # Добавляем в инвентарь
    if 'inventory' not in user_data:
        user_data['inventory'] = {}
    
    gift_id = winner_item_data['id']
    if gift_id not in user_data['inventory']:
        user_data['inventory'][gift_id] = 0
    user_data['inventory'][gift_id] += 1
    
    # Добавляем опыт
    user_data['experience'] += gift_data['stars'] // 10
    
    # Показываем результат
    keyboard = {
        "inline_keyboard": [
            [{"text": "🎁 Открыть еще", "callback_data": f"open_{case_id}"}],
            [{"text": "🔙 К кейсам", "callback_data": "gift_shop"}]
        ]
    }
    
    rarity = get_rarity_from_stars(gift_data['stars'])
    rarity_names = {
        "common": "⚪ Обычный",
        "uncommon": "🟢 Необычный", 
        "rare": "🔵 Редкий",
        "epic": "🟣 Эпический",
        "legendary": "🟡 Легендарный",
        "mythic": "🔴 Мифический"
    }
    
    text = f"""🎉 <b>Кейс открыт!</b>

{gift_data['emoji']} <b>{gift_data['name']}</b>
⭐ <b>Стоимость:</b> {gift_data['stars']} звезд
{rarity_names[rarity]} <b>({rarity.upper()})</b>

💰 <b>Новый баланс:</b> {user_data['balance']} монет
📦 <b>Кейсов открыто:</b> {user_data['cases_opened']}

🎁 <b>Подарок добавлен в инвентарь!</b>"""
    
    edit_message(chat_id, message_id, text, keyboard)

def get_random_item_from_case(case):
    """Получить случайный предмет из кейса с учетом шансов"""
    total_chance = sum(item['chance'] for item in case['items'])
    random_value = random.random() * total_chance
    
    current_chance = 0
    for item in case['items']:
        current_chance += item['chance']
        if random_value <= current_chance:
            return item
    
    return case['items'][0]  # fallback

def get_rarity_from_stars(stars):
    """Определить редкость по количеству звезд"""
    if stars <= 25:
        return "common"
    elif stars <= 100:
        return "uncommon"
    elif stars <= 500:
        return "rare"
    elif stars <= 1000:
        return "epic"
    elif stars <= 2000:
        return "legendary"
    else:
        return "mythic"

def handle_daily_bonus(chat_id, message_id):
    user_data = get_user_data(chat_id)
    
    # Проверяем, можно ли получить бонус
    now = datetime.now()
    last_bonus = user_data.get('last_bonus')
    
    if last_bonus:
        last_bonus_date = datetime.fromisoformat(last_bonus)
        if (now - last_bonus_date).days < 1:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main"}]
                ]
            }
            hours_left = 24 - (now - last_bonus_date).seconds // 3600
            text = f"""⏰ <b>Ежедневный бонус уже получен!</b>

Следующий бонус через {hours_left} часов

💰 <b>Текущий баланс:</b> {user_data['balance']} монет"""
            edit_message(chat_id, message_id, text, keyboard)
            return
    
    # Выдаем бонус
    bonus_amount = random.randint(100, 500)
    user_data['balance'] += bonus_amount
    user_data['last_bonus'] = now.isoformat()
    user_data['experience'] += 50
    
    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 Играть", "callback_data": "play_crash"}],
            [{"text": "🏠 Главное меню", "callback_data": "main"}]
        ]
    }
    
    text = f"""🎉 <b>Ежедневный бонус получен!</b>

💰 <b>Получено:</b> {bonus_amount} монет
⭐ <b>Получено XP:</b> 50
💳 <b>Новый баланс:</b> {user_data['balance']} монет

🎁 Возвращайтесь завтра за новым бонусом!"""

    edit_message(chat_id, message_id, text, keyboard)

def game_loop():
    global current_crash_game
    
    while True:
        try:
            with game_lock:
                current_crash_game = CrashGame()
                
                # Ожидание между играми
                time.sleep(10)
                
                # Запуск новой игры
                current_crash_game.start_round()
                
                # Игровой цикл
                while current_crash_game.is_running and not current_crash_game.is_crashed:
                    current_crash_game.update_multiplier()
                    
                    # Проверка авто-вывода
                    for user_id in list(current_crash_game.bets.keys()):
                        bet_info = current_crash_game.bets[user_id]
                        if (bet_info.get('auto_cashout') and 
                            current_crash_game.multiplier >= bet_info['auto_cashout'] and
                            user_id not in current_crash_game.cashed_out):
                            current_crash_game.cashout(user_id)
                    
                    time.sleep(0.1)
                
                # Обеспечиваем краш если игра завершилась не крашем
                if not current_crash_game.is_crashed:
                    current_crash_game.crash()
                
                # Пауза после краша
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Game loop error: {e}")
            time.sleep(5)

# Запуск игрового цикла в отдельном потоке
game_thread = threading.Thread(target=game_loop)
game_thread.daemon = True
game_thread.start()

@app.route("/")
def home():
    return """
    <h1>🎁 GiftBot Crash Game 🚀</h1>
    <p>Telegram bot в стиле GiftUp</p>
    """

def handle_webhook_callback(chat_id, message_id, callback_data, user_name):
    try:
        if callback_data == "main":
            user_data = get_user_data(chat_id)
            text = f"""🎁 <b>GiftBot - {user_name}</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} ({user_data['experience']} XP)

Выберите действие:"""
            edit_message(chat_id, message_id, text, main_menu_keyboard())
            
        elif callback_data == "play_crash":
            handle_crash_game(chat_id, message_id)
            
        elif callback_data.startswith("bet_"):
            amount = int(callback_data.split("_")[1])
            handle_bet(chat_id, message_id, amount)
            
        elif callback_data == "cashout":
            handle_cashout(chat_id, "")
            handle_crash_game(chat_id, message_id)
            
        elif callback_data == "gift_shop":
            handle_gift_shop(chat_id, message_id)
            
        elif callback_data.startswith("open_"):
            case_id = callback_data.replace("open_", "")
            open_case(chat_id, message_id, case_id)
            
        elif callback_data == "daily_bonus":
            handle_daily_bonus(chat_id, message_id)
            
        elif callback_data in ["balance", "stats"]:
            user_data = get_user_data(chat_id)
            win_rate = (user_data['games_won'] / max(user_data['games_played'], 1)) * 100
            
            inventory_count = sum(user_data.get('inventory', {}).values())
            total_stars = 0
            for gift_id, count in user_data.get('inventory', {}).items():
                if gift_id in REAL_TELEGRAM_GIFTS:
                    total_stars += REAL_TELEGRAM_GIFTS[gift_id]['stars'] * count
            
            text = f"""📊 <b>Статистика - {user_name}</b>

💰 <b>Баланс:</b> {user_data['balance']} монет
🎯 <b>Уровень:</b> {user_data['level']} (XP: {user_data['experience']})

🎮 <b>Игровая статистика:</b>
• Игр сыграно: {user_data['games_played']}
• Побед: {user_data['games_won']}
• Поражений: {user_data['games_lost']}
• Винрейт: {win_rate:.1f}%

💸 <b>Финансы:</b>
• Поставлено: {user_data['total_bet']} монет
• Выиграно: {user_data['total_won']} монет
• Потеряно: {user_data['total_lost']} монет

🎁 <b>Коллекция:</b>
• Подарков: {inventory_count}
• Кейсов открыто: {user_data.get('cases_opened', 0)}
• Общая стоимость: {total_stars} звезд"""

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🚀 Играть", "callback_data": "play_crash"}],
                    [{"text": "🔙 Назад", "callback_data": "main"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            
        elif callback_data == "referrals":
            user_data = get_user_data(chat_id)
            referral_count = len(user_data.get('referrals', []))
            
            text = f"""👥 <b>Реферальная система</b>

👥 <b>Ваши рефералы:</b> {referral_count}
💰 <b>Заработано:</b> {referral_count * 500} монет

🔗 <b>Ваша реферальная ссылка:</b>
https://t.me/lambo_gift_bot?start={chat_id}

💡 <b>За каждого реферала:</b>
• Вы получаете 500 монет
• Реферал получает 200 монет"""

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 Назад", "callback_data": "main"}]
                ]
            }
            edit_message(chat_id, message_id, text, keyboard)
            
    except Exception as e:
        logger.error(f"Callback handling error: {e}")
