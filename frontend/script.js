
document.addEventListener('DOMContentLoaded', () => {

    // Configuration
    const API_BASE_URL = 'http://localhost:8000'; // Ensure your FastAPI backend runs here

    lucide.createIcons();

    // State
    let isFileUploaded = false;
    let currentSourcePath = null; // Store backend path
    let isSystemUnlocked = false;

    // Elements
    const ingestCard = document.querySelector('.card-ingest');
    const summarizerCard = document.querySelector('.card-summary');
    const quizCard = document.querySelector('.card-quiz');
    const modal = document.getElementById('summarizer-modal');
    const closeModal = document.querySelector('.close-modal');
    const modeBtns = document.querySelectorAll('.mode-btn');
    const outputConsole = document.getElementById('summary-output');
    const statusDot = document.querySelector('.status-indicator');

    // =========================================
    // 1. UNIVERSAL INGEST & UPLOAD
    // =========================================

    // Elements
    const ingestInitial = document.getElementById('ingest-initial');
    const ingestGrid = document.getElementById('ingest-grid');
    const ingestTabs = document.getElementById('ingest-tabs');
    const ingestActive = document.getElementById('ingest-active');
    const ingestBack = document.getElementById('ingest-back-btn');

    // Auth Check Helper
    function checkAuth() {
        if (!isSystemUnlocked) {
            const mModal = document.getElementById('model-modal'); // Assuming standard settings modal usage
            // Trigger API key requirement if not set
            const lockIcon = document.getElementById('api-lock-icon');
            lockIcon.style.color = "red";
            setTimeout(() => lockIcon.style.color = "", 500); // Blink red

            // Focus API key field
            if (document.getElementById('inline-api-key')) {
                document.getElementById('inline-api-key').focus();
            } else {
                alert("Please initialize with API Key first.");
            }
            return false;
        }
        return true;
    }

    // Helper: Upload File to Backend
    async function uploadFileToBackend(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            ingestCard.style.opacity = '0.7'; // Loading visual

            const response = await fetch(`${API_BASE_URL}/api/upload`, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) throw new Error('Upload failed');

            const data = await response.json();
            currentSourcePath = data.file_path; // Save server path
            isFileUploaded = true;

            ingestCard.style.borderColor = "#00FF00";
            alert(`File "${file.name}" ready for processing.`);
        } catch (error) {
            console.error(error);
            alert("Error uploading file: " + error.message);
            ingestCard.style.borderColor = "red";
        } finally {
            ingestCard.style.opacity = '1';
        }
    }

    // 1.1 Initial Click -> Show Grid
    ingestInitial.addEventListener('click', (e) => {
        if (!checkAuth()) return;
        ingestInitial.classList.add('hidden');
        ingestGrid.classList.remove('hidden');
        ingestBack.classList.remove('hidden');
        ingestTabs.classList.add('hidden');
        ingestActive.classList.add('hidden');
    });

    // 1.x Back Button
    ingestBack.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!ingestActive.classList.contains('hidden')) {
            ingestTabs.classList.add('hidden');
            ingestActive.classList.add('hidden');
            ingestGrid.classList.remove('hidden');
        } else if (!ingestGrid.classList.contains('hidden')) {
            ingestGrid.classList.add('hidden');
            ingestInitial.classList.remove('hidden');
            ingestBack.classList.add('hidden');
        }
    });

    // 1.2 Grid Selection
    document.querySelectorAll('.grid-tile').forEach(tile => {
        tile.addEventListener('click', () => {
            const type = tile.dataset.type;
            ingestGrid.classList.add('hidden');
            ingestTabs.classList.remove('hidden');
            ingestActive.classList.remove('hidden');

            // Basic UI switch for tabs (Files default)
            document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
            const filesTab = document.querySelector('.tab-item[data-tab="files"]');
            if (filesTab) filesTab.classList.add('active');

            document.getElementById('mode-files').classList.remove('hidden');
            document.getElementById('mode-links').classList.add('hidden');
            if (type === 'weblink' || type === 'search') {
                document.querySelector('.tab-item[data-tab="links"]').click();
            }
        });
    });

    // Tab Switching
    document.querySelectorAll('.tab-item').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const target = tab.dataset.tab;
            document.querySelectorAll('.input-mode').forEach(m => m.classList.add('hidden'));
            document.getElementById(`mode-${target}`).classList.remove('hidden');
        });
    });


    // File Drop Zone Logic
    const dropZone = document.querySelector('.drop-zone');
    if (dropZone) {
        dropZone.addEventListener('click', () => {
            // Check auth again strictly
            // if (!checkAuth()) return; 

            const input = document.createElement('input');
            input.type = 'file';
            input.click();
            input.onchange = (e) => {
                const file = e.target.files[0];
                if (file) {
                    uploadFileToBackend(file);
                }
            };
        });
    }

    // Link/Text Input
    const linkInput = document.getElementById('link-input');
    if (linkInput) {
        linkInput.addEventListener('change', (e) => {
            if (e.target.value.trim().length > 0) {
                currentSourcePath = e.target.value.trim();
                isFileUploaded = true;
                alert("Topic/Link set as source.");
            }
        });
    }


    // =========================================
    // 2. SUMMARIZER LOGIC (REAL API)
    // =========================================
    summarizerCard.addEventListener('click', () => {
        if (!isFileUploaded || !currentSourcePath) {
            alert("ACCESS DENIED: Please ingest a document or link first.");
            return;
        }
        modal.classList.remove('hidden');
        setTimeout(() => modal.classList.add('active'), 10);
    });

    closeModal.addEventListener('click', () => {
        modal.classList.remove('active');
        setTimeout(() => {
            modal.classList.add('hidden');
            outputConsole.innerHTML = '<p class="placeholder-text">// Select a mode to begin processing...</p>';
            modeBtns.forEach(b => b.classList.remove('active'));
        }, 300);
    });

    // Mode Selection -> Trigger API
    modeBtns.forEach(btn => {
        btn.addEventListener('click', async () => {
            modeBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const mode = btn.getAttribute('data-mode'); // concise, detailed, etc.

            outputConsole.innerHTML = "<div class='blink'>_ AGENT ANALYZING & GENERATING...</div>";

            try {
                const response = await fetch(`${API_BASE_URL}/api/process`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        source_path: currentSourcePath,
                        mode: "summarize",
                        summary_type: mode
                    })
                });

                if (!response.ok) throw new Error("Processing failed");

                const result = await response.json();

                // Render Result
                outputConsole.innerHTML = "";
                const text = result.result;

                // Simple typewriter
                let i = 0;
                function typeWriter() {
                    if (i < text.length) {
                        outputConsole.innerHTML += text.charAt(i);
                        i++;
                        setTimeout(typeWriter, 2);
                    }
                }
                typeWriter();

            } catch (e) {
                outputConsole.innerHTML = `<span style="color:red">ERROR: ${e.message}</span>`;
            }
        });
    });

    // =========================================
    // 3. QUIZ GENERATOR LOGIC (REAL API)
    // =========================================
    const quizModal = document.getElementById('quiz-modal');
    const quizClose = document.querySelector('.quiz-close');
    const quizOutput = document.getElementById('quiz-output');
    const generateBtn = document.getElementById('generate-quiz-btn');
    const diffBtns = document.querySelectorAll('.diff-btn');
    const countSlider = document.getElementById('q-count-slider');
    const countDisplay = document.getElementById('q-count-display');

    let quizConfig = { difficulty: 'Medium', count: 5 };

    quizCard.addEventListener('click', () => {
        if (!isFileUploaded || !currentSourcePath) {
            alert("ACCESS DENIED: Please ingest data first.");
            return;
        }
        quizModal.classList.remove('hidden');
        setTimeout(() => quizModal.classList.add('active'), 10);
    });

    quizClose.addEventListener('click', () => {
        quizModal.classList.remove('active');
        setTimeout(() => quizModal.classList.add('hidden'), 300);
    });

    diffBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            diffBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            quizConfig.difficulty = btn.dataset.level;
        });
    });

    countSlider.addEventListener('input', (e) => {
        quizConfig.count = parseInt(e.target.value);
        countDisplay.textContent = quizConfig.count;
    });

    generateBtn.addEventListener('click', async () => {
        generateBtn.innerHTML = `GENERATING... <i data-lucide="loader-2" class="spin"></i>`;
        quizOutput.innerHTML = "<div class='blink'>_ AGENT RESEARCHING & GENERATING QUESTIONS...</div>";

        try {
            const response = await fetch(`${API_BASE_URL}/api/process`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_path: currentSourcePath,
                    mode: "quiz",
                    num_questions: quizConfig.count,
                    difficulty: quizConfig.difficulty
                })
            });

            if (!response.ok) throw new Error("Generation failed");

            const data = await response.json();
            const questions = data.result;

            renderQuiz(questions);

        } catch (e) {
            quizOutput.innerHTML = `<span style="color:red">ERROR: ${e.message}</span>`;
        } finally {
            generateBtn.innerHTML = `GENERATE QUIZ <i data-lucide="zap" class="btn-icon"></i>`;
            lucide.createIcons();
        }
    });

    function renderQuiz(questions) {
        quizOutput.innerHTML = "";
        if (!questions || questions.length === 0) {
            quizOutput.innerHTML = "No questions generated.";
            return;
        }

        questions.forEach((q, index) => {
            const card = document.createElement('div');
            card.className = 'question-card';
            card.style.animationDelay = `${index * 0.1}s`;

            const qNum = index + 1;
            const qId = `q${qNum}`;

            card.innerHTML = `
                <div class="q-header">
                    <span class="q-num">${String(qNum).padStart(2, '0')}</span>
                    <span class="q-badge">${quizConfig.difficulty}</span>
                </div>
                <p class="q-text">${q.question}</p>
                <div class="q-options">
                    ${q.options.map((opt, i) => `
                        <button class="option-btn" onclick="selectOption(this)">
                            ${String.fromCharCode(65 + i)}) ${opt}
                        </button>
                    `).join('')}
                </div>
                <div class="q-footer">
                    <button class="reveal-btn" onclick="toggleAnswer('ans-${qId}')">REVEAL ANSWER</button>
                    <div id="ans-${qId}" class="answer-panel hidden">
                        <strong>Correct Answer:</strong> ${q.correct_answer}
                        <br><br>
                        <em>${q.explanation}</em>
                    </div>
                </div>
            `;
            quizOutput.appendChild(card);
        });
    }

    // Global Helpers 
    window.toggleAnswer = (id) => {
        const el = document.getElementById(id);
        if (el) el.classList.toggle('hidden');
    };
    window.selectOption = (btn) => {
        const parent = btn.parentElement;
        parent.querySelectorAll('.option-btn').forEach(b => {
            b.style.borderColor = '#444';
            b.style.color = '#ccc';
        });
        btn.style.borderColor = '#F8311C';
        btn.style.color = 'white';
    };


    // =========================================
    // 4. SETTINGS & INITIALIZATION (API KEY)
    // =========================================
    const apiKeyField = document.getElementById('inline-api-key');
    const lockIcon = document.getElementById('api-lock-icon');
    const modelModal = document.getElementById('model-modal'); // Assuming this ID exists
    const modelCards = document.querySelectorAll('.model-card');

    if (apiKeyField) {
        apiKeyField.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                const key = e.target.value;
                if (key.length > 5) {
                    // UI Loading
                    lockIcon.setAttribute('data-lucide', 'loader-2');
                    lockIcon.classList.add('spin');
                    lockIcon.style.color = "#FF8C00";
                    lucide.createIcons();

                    // Call Backend Init
                    try {
                        const res = await fetch(`${API_BASE_URL}/api/init`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ api_key: key, model_name: "gemini-2.0-flash" })
                        });
                        if (!res.ok) console.warn("Backend handshake failed, proceeding in offline mode.");
                    } catch (err) {
                        console.warn("Backend unavailable, proceeding in offline mode.");
                    }

                    // Always unlock to maintain flow
                    isSystemUnlocked = true;

                    // Re-query element because lucide.createIcons() replaces the node
                    const activeLockIcon = document.getElementById('api-lock-icon');
                    if (activeLockIcon) {
                        activeLockIcon.setAttribute('data-lucide', 'unlock');
                        activeLockIcon.classList.remove('spin');
                        activeLockIcon.style.color = "#00FF00";
                        lucide.createIcons();
                    }

                    // Unlock visual elements
                    document.querySelectorAll('.locked').forEach(c => c.classList.remove('locked'));

                    // Show Model Modal if desired
                    if (modelModal) {
                        modelModal.classList.remove('hidden');
                        setTimeout(() => modelModal.classList.add('active'), 10);
                    }
                }
            }
        });
    }

    // Model Card Selection
    modelCards.forEach(card => {
        card.addEventListener('click', () => {
            if (card.classList.contains('disabled')) return;
            modelCards.forEach(c => c.classList.remove('active'));
            card.classList.add('active');

            // Close modal
            if (modelModal) {
                modelModal.classList.remove('active');
                setTimeout(() => modelModal.classList.add('hidden'), 300);
            }
        });
    });

});
