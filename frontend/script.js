
document.addEventListener('DOMContentLoaded', () => {

    // Configuration
    const API_BASE_URL = 'http://localhost:8000'; // Ensure your FastAPI backend runs here

    lucide.createIcons();

    // State
    let isFileUploaded = false;
    let currentSourcePath = null; // Store backend path
    let isSystemUnlocked = false;
    let currentApiKey = null;
    let currentModel = "gemini-2.5-flash"; // Default Model

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

        // State 3: Active Input -> State 2: Grid
        if (!ingestActive.classList.contains('hidden')) {
            console.log("Back: Active -> Grid");
            ingestTabs.classList.add('hidden');
            ingestActive.classList.add('hidden');
            ingestGrid.classList.remove('hidden');
            // Reset contents
            document.querySelectorAll('.input-mode').forEach(el => el.classList.add('hidden'));
        }
        // State 2: Grid -> State 1: Initial
        else if (!ingestGrid.classList.contains('hidden')) {
            console.log("Back: Grid -> Initial");
            ingestGrid.classList.add('hidden');
            ingestInitial.classList.remove('hidden');
            ingestBack.classList.add('hidden');
        }
    });

    // 1.2 Grid Selection
    document.querySelectorAll('.grid-tile').forEach(tile => {
        tile.addEventListener('click', () => {
            const type = tile.dataset.type;

            // Transition: Grid -> Active
            ingestGrid.classList.add('hidden');
            ingestTabs.classList.remove('hidden');
            ingestActive.classList.remove('hidden');

            // Elements
            const filesTab = document.querySelector('.tab-item[data-tab="files"]');
            const textTab = document.querySelector('.tab-item[data-tab="text"]');
            const linksTab = document.querySelector('.tab-item[data-tab="links"]');

            const modeFiles = document.getElementById('mode-files');
            const modeText = document.getElementById('mode-text');
            const modeLinks = document.getElementById('mode-links');
            const modeYoutube = document.getElementById('mode-youtube');

            // Reset All Tabs & Modes first
            [filesTab, textTab, linksTab].forEach(t => {
                if (t) { t.style.display = 'none'; t.classList.remove('active'); }
            });
            [modeFiles, modeText, modeLinks, modeYoutube].forEach(m => {
                if (m) m.classList.add('hidden');
            });

            // Reset all custom overrides first
            if (filesTab) delete filesTab.dataset.targetMode;

            // Logic per Type
            if (type === 'documents') {
                // "docs --- documents and text"
                if (filesTab) {
                    filesTab.style.display = 'block';
                    filesTab.innerText = '[DOCUMENTS]';
                    filesTab.classList.add('active'); // Default
                }
                if (textTab) textTab.style.display = 'block';

                // Show Default Mode
                modeFiles.classList.remove('hidden');
            }
            else if (type === 'visuals') {
                // "visuals-- only images"
                if (filesTab) {
                    filesTab.style.display = 'block';
                    filesTab.innerText = '[IMAGES]';
                    filesTab.classList.add('active'); // Default
                }
                // Show Default Mode
                modeFiles.classList.remove('hidden');
            }
            else if (type === 'search') {
                if (filesTab) {
                    filesTab.style.display = 'block';
                    filesTab.innerText = '[QUERY]';
                    filesTab.classList.add('active'); // Default to Query for Search
                    filesTab.dataset.targetMode = 'search-query'; // custom indicator
                }
                if (textTab) {
                    textTab.style.display = 'none';
                }
                if (linksTab) {
                    linksTab.style.display = 'block';
                    linksTab.innerText = '[LINKS]';
                    linksTab.classList.remove('active');
                }
                // Show Query Mode by default
                document.getElementById('mode-search-query').classList.remove('hidden');
            }
            else if (type === 'youtube') {
                // "youtube - only url input"
                if (filesTab) filesTab.style.display = 'none';
                if (textTab) textTab.style.display = 'none';
                if (linksTab) linksTab.style.display = 'none';

                ingestTabs.classList.add('hidden'); // No tabs needed for single mode

                // Show Default Mode
                modeYoutube.classList.remove('hidden');
            }
        });
    });

    // Tab Switching
    document.querySelectorAll('.tab-item').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.tab-item').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            const target = tab.dataset.tab;
            // Hide all modes
            document.querySelectorAll('.input-mode').forEach(m => m.classList.add('hidden'));

            // Show specific mode
            // Check if tab has a special target override (like Query -> mode-search-query)
            let modeId = `mode-${target}`;
            if (tab.dataset.targetMode) {
                modeId = `mode-${tab.dataset.targetMode}`;
            }

            const modeEl = document.getElementById(modeId);
            if (modeEl) modeEl.classList.remove('hidden');
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

    // Text Input Processing
    const processTextBtn = document.getElementById('process-text-btn');
    if (processTextBtn) {
        processTextBtn.addEventListener('click', () => {
            const textarea = document.querySelector('.ingest-textarea');
            const content = textarea.value.trim();

            if (content.length === 0) {
                alert("Please enter some text first.");
                return;
            }

            // Create a virtual file to reuse the upload logic
            const blob = new Blob([content], { type: 'text/plain' });
            const file = new File([blob], "raw_text_input.txt", { type: "text/plain" });

            // Visual feedback
            processTextBtn.innerHTML = 'UPLOADING...';

            uploadFileToBackend(file).then(() => {
                processTextBtn.innerHTML = 'PROCESS <i data-lucide="check" style="display:inline; width:16px;"></i>';
                setTimeout(() => {
                    processTextBtn.innerHTML = 'PROCESS <i data-lucide="arrow-right" style="display:inline; width:16px;"></i>';
                    textarea.value = ""; // Clear input
                    // Hide active area to show it's done? Or just alert?
                    // alert("Text ingested successfully!"); 
                }, 1000);
            });
        });
    }


    // Search Query Processing
    const processQueryBtn = document.getElementById('process-query-btn');
    if (processQueryBtn) {
        processQueryBtn.addEventListener('click', () => {
            const inputField = document.getElementById('search-query-field');
            const query = inputField.value.trim();

            if (query.length === 0) {
                alert("Please enter a search query.");
                return;
            }

            // Set state directly
            currentSourcePath = query; // Backend will treat non-file/non-url as Search Query
            isFileUploaded = true;

            // Visual Feedback
            processQueryBtn.innerHTML = 'SEARCHING... <i data-lucide="loader-2" class="spin" style="display:inline; width:16px;"></i>';
            lucide.createIcons();
            ingestCard.style.borderColor = "#00FF00";

            setTimeout(() => {
                processQueryBtn.innerHTML = 'READY <i data-lucide="check" style="display:inline; width:16px;"></i>';
                lucide.createIcons();
                setTimeout(() => {
                    processQueryBtn.innerHTML = 'SEARCH <i data-lucide="search" style="display:inline; width:16px;"></i>';
                    lucide.createIcons();
                }, 2000);
            }, 1000);
        });
    }

    // Link Input Processing
    const processLinkBtn = document.getElementById('process-link-btn');
    if (processLinkBtn) {
        processLinkBtn.addEventListener('click', () => {
            const inputField = document.getElementById('link-input-field');
            const url = inputField.value.trim();

            if (url.length === 0) {
                alert("Please enter a valid URL.");
                return;
            }

            // Set state directly
            currentSourcePath = url;
            isFileUploaded = true;

            // Visual Feedback
            processLinkBtn.innerHTML = 'LINKED <i data-lucide="check" style="display:inline; width:16px;"></i>';
            ingestCard.style.borderColor = "#00FF00";

            setTimeout(() => {
                processLinkBtn.innerHTML = 'PROCESS <i data-lucide="arrow-right" style="display:inline; width:16px;"></i>';
            }, 1000);
        });
    }

    // YouTube Input Processing
    const processYoutubeBtn = document.getElementById('process-youtube-btn');
    if (processYoutubeBtn) {
        processYoutubeBtn.addEventListener('click', () => {
            const inputField = document.getElementById('youtube-input-field');
            const rawUrl = inputField.value.trim();
            const urlLower = rawUrl.toLowerCase();

            console.log("YouTube Extract Clicked for:", rawUrl);

            // Case-insensitive check
            if (rawUrl.length === 0 || (!urlLower.includes("youtube.com") && !urlLower.includes("youtu.be"))) {
                alert("Please enter a valid YouTube URL (e.g., youtube.com/watch?v=...)");
                return;
            }

            // Set state 
            currentSourcePath = rawUrl; // Use original casing for backend
            isFileUploaded = true;

            // Visual Feedback
            processYoutubeBtn.innerHTML = 'EXTRACTING... <i data-lucide="loader-2" class="spin" style="display:inline; width:16px;"></i>';
            lucide.createIcons();
            ingestCard.style.borderColor = "#ff0000";

            // We can trigger an optional pre-fetch here if we wanted to validate instantly, 
            // but for now we just verify it sets the path correctly for the RAG step.

            setTimeout(() => {
                processYoutubeBtn.innerHTML = 'READY <i data-lucide="check" style="display:inline; width:16px;"></i>';
                lucide.createIcons();
                setTimeout(() => {
                    processYoutubeBtn.innerHTML = 'EXTRACT <i data-lucide="youtube" style="display:inline; width:16px;"></i>';
                    lucide.createIcons();
                }, 2000);
            }, 1500);
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
                        summary_type: mode,
                        model_name: currentModel // Pass selected model
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
                    difficulty: quizConfig.difficulty,
                    model_name: currentModel // Pass selected model
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

                    currentApiKey = key;

                    // Call Backend Init
                    try {
                        const res = await fetch(`${API_BASE_URL}/api/init`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ api_key: key, model_name: currentModel })
                        });

                        if (res.ok) {
                            const data = await res.json();
                            // Update Model Grid with real models
                            if (data.models && Array.isArray(data.models)) {
                                const grid = document.querySelector('.model-grid');
                                if (grid) {
                                    grid.innerHTML = ''; // Clear placeholders
                                    data.models.forEach(modelName => {
                                        const btn = document.createElement('button');
                                        btn.className = 'model-card';
                                        btn.dataset.model = modelName;

                                        // Format Name
                                        // e.g. gemini-1.5-pro -> GEMINI / 1.5 PRO
                                        let name = modelName.toUpperCase();
                                        let tag = "AI";

                                        if (name.includes('GEMINI')) {
                                            const parts = name.split('-');
                                            name = parts[0];
                                            tag = parts.slice(1).join(' ');
                                        }

                                        btn.innerHTML = `
                                            <span class="model-name">${name}</span>
                                            <span class="model-tag">${tag}</span>
                                        `;

                                        // Attach selection logic
                                        btn.addEventListener('click', async () => {
                                            document.querySelectorAll('.model-card').forEach(c => c.classList.remove('active'));
                                            btn.classList.add('active');
                                            btn.style.borderColor = "#00FF00"; // Immediate visual feedback

                                            // Model Selection Logic (Local State)
                                            currentModel = modelName;
                                            console.log("Model saved locally:", currentModel);

                                            // Helper to close modal
                                            const closeModal = () => {
                                                setTimeout(() => {
                                                    const modalToClose = document.getElementById('model-modal');
                                                    if (modalToClose) {
                                                        modalToClose.classList.remove('active');
                                                        setTimeout(() => modalToClose.classList.add('hidden'), 300);
                                                    }
                                                }, 500);
                                            };

                                            // Switch Active Model on Backend (Optional but good for persistent session)
                                            if (currentApiKey) {
                                                console.log("Switching model to:", modelName);
                                                try {
                                                    await fetch(`${API_BASE_URL}/api/init`, {
                                                        method: 'POST',
                                                        headers: { 'Content-Type': 'application/json' },
                                                        body: JSON.stringify({ api_key: currentApiKey, model_name: modelName })
                                                    });
                                                } catch (err) {
                                                    console.error("Model switch API failed", err);
                                                }
                                            } else {
                                                console.warn("No API key present, selecting UI only.");
                                            }

                                            // ALWAYS close
                                            closeModal();
                                        });

                                        grid.appendChild(btn);
                                    });
                                }
                            }
                        } else {
                            console.warn("Backend handshake failed, proceeding in offline mode.");
                        }
                    } catch (err) {
                        console.warn("Backend unavailable, proceeding in offline mode.", err);
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

    // Model Card Selection (For initial static cards if any)
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



    // =========================================
    // 5. MODEL SEARCH FUNCTIONALITY
    // =========================================
    const modelSearchInput = document.getElementById('model-search');
    if (modelSearchInput) {
        modelSearchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            // Re-query cards as they might be dynamic
            const cards = document.querySelectorAll('.model-card');

            cards.forEach(card => {
                const modelName = card.dataset.model ? card.dataset.model.toLowerCase() : '';
                const textContent = card.innerText.toLowerCase();

                if (modelName.includes(query) || textContent.includes(query)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // Close Settings Modal specifically
    const settingsCloseBtn = document.querySelector('.settings-close');
    if (settingsCloseBtn && modelModal) {
        settingsCloseBtn.addEventListener('click', () => {
            modelModal.classList.remove('active');
            setTimeout(() => modelModal.classList.add('hidden'), 300);
        });
    }

});
