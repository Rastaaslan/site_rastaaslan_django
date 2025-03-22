/**
 * JavaScript pour les fonctionnalités améliorées du forum
 */
document.addEventListener('DOMContentLoaded', function() {
    // =======================================================
    // Gestion des réactions aux messages
    // =======================================================
    function setupReactions() {
        // Récupérer tous les boutons de réaction
        const reactionButtons = document.querySelectorAll('.reaction-btn, .dropdown-item[data-reaction]');
        
        reactionButtons.forEach(button => {
            button.addEventListener('click', function() {
                if (!this.dataset.reaction || !this.dataset.postId) return;
                
                const reactionType = this.dataset.reaction;
                const postId = this.dataset.postId;
                
                // Envoyer la requête AJAX
                const formData = new FormData();
                formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
                formData.append('reaction_type', reactionType);
                
                fetch(`/forum/post/${postId}/react/`, {
                    method: 'POST',
                    body: formData,
                    credentials: 'same-origin'
                })
                .then(response => response.json())
                .then(data => {
                    // Mettre à jour l'interface
                    updateReactions(postId, data.reactions, data.reaction_emojis);
                })
                .catch(error => console.error('Error:', error));
            });
        });
    }
    
    // Mettre à jour l'affichage des réactions
    function updateReactions(postId, reactions, emojis) {
        const reactionsContainer = document.querySelector(`.post-reactions[data-post-id="${postId}"]`);
        if (!reactionsContainer) return;
        
        // Nettoyer le conteneur (en conservant le bouton d'ajout)
        const addButton = reactionsContainer.querySelector('.dropdown');
        reactionsContainer.innerHTML = '';
        
        // Ajouter les nouvelles réactions
        for (const [type, count] of Object.entries(reactions)) {
            const button = document.createElement('button');
            button.className = 'reaction-btn';
            button.dataset.reaction = type;
            button.dataset.postId = postId;
            
            // Vérifier si l'utilisateur a réagi
            if (document.querySelector(`.reaction-btn.active[data-reaction="${type}"][data-post-id="${postId}"]`)) {
                button.classList.add('active');
            }
            
            // Emoji
            const emoji = document.createElement('span');
            emoji.className = 'emoji';
            emoji.textContent = getEmoji(type);
            
            // Compteur
            const countSpan = document.createElement('span');
            countSpan.className = 'count';
            countSpan.textContent = count;
            
            button.appendChild(emoji);
            button.appendChild(countSpan);
            reactionsContainer.appendChild(button);
        }
        
        // Remettre le bouton d'ajout
        if (addButton) {
            reactionsContainer.appendChild(addButton);
        }
        
        // Réattacher les événements
        setupReactions();
    }
    
    // Helper pour obtenir l'emoji correspondant au type de réaction
    function getEmoji(type) {
        const emojis = {
            'like': '👍',
            'thanks': '🙏',
            'funny': '😂',
            'insightful': '💡'
        };
        return emojis[type] || '👍';
    }
    
    // =======================================================
    // Fonction pour citer un message
    // =======================================================
    function setupQuoteButtons() {
        const quoteButtons = document.querySelectorAll('.quote-post');
        quoteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const username = this.dataset.username;
                const content = this.dataset.content;
                
                const textarea = document.querySelector('#id_content');
                const quotedText = `> **@${username} a écrit :**\n> ${content.split('\n').join('\n> ')}\n\n`;
                
                textarea.value += quotedText;
                textarea.focus();
                
                // Mettre à jour la prévisualisation si elle est active
                if (document.getElementById('preview-toggle').checked) {
                    updatePreview();
                }
            });
        });
    }
    
    // =======================================================
    // Mise en évidence des mentions
    // =======================================================
    function highlightMentions() {
        document.querySelectorAll('.markdown-content').forEach(container => {
            const html = container.innerHTML;
            const updatedHtml = html.replace(/@(\w+)/g, '<span class="post-mention">@$1</span>');
            container.innerHTML = updatedHtml;
        });
    }
    
    // =======================================================
    // Prévisualisation Markdown
    // =======================================================
    function setupMarkdownPreview() {
        const previewToggle = document.getElementById('preview-toggle');
        const previewContainer = document.querySelector('.preview-container');
        const previewContent = document.getElementById('preview-content');
        const contentTextarea = document.getElementById('id_content');
        
        if (previewToggle && previewContainer && previewContent && contentTextarea) {
            previewToggle.addEventListener('change', function() {
                if (this.checked) {
                    // Afficher la prévisualisation
                    previewContainer.classList.remove('d-none');
                    updatePreview();
                } else {
                    // Masquer la prévisualisation
                    previewContainer.classList.add('d-none');
                }
            });
            
            // Mettre à jour la prévisualisation lors de la saisie (avec debounce)
            let previewTimeout;
            contentTextarea.addEventListener('input', function() {
                if (previewToggle.checked) {
                    clearTimeout(previewTimeout);
                    previewTimeout = setTimeout(updatePreview, 500);
                }
            });
        }
    }
    
    // Fonction pour mettre à jour la prévisualisation
    function updatePreview() {
        const textarea = document.getElementById('id_content');
        const previewContent = document.getElementById('preview-content');
        
        if (!textarea || !previewContent) return;
        
        const formData = new FormData();
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        formData.append('content', textarea.value);
        
        fetch('/forum/markdown/preview/', {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            previewContent.innerHTML = data.html;
            // Mettre à jour les mentions dans la prévisualisation
            highlightMentions();
        })
        .catch(error => console.error('Error:', error));
    }
    
    // =======================================================
    // Boutons de formatage Markdown
    // =======================================================
    function setupMarkdownButtons() {
        const markdownButtons = document.querySelectorAll('.markdown-btn');
        markdownButtons.forEach(button => {
            button.addEventListener('click', function() {
                const format = this.dataset.format;
                const textarea = document.querySelector('#id_content');
                const start = textarea.selectionStart;
                const end = textarea.selectionEnd;
                const selectedText = textarea.value.substring(start, end);
                
                let formattedText = '';
                
                switch (format) {
                    case 'bold':
                        formattedText = `**${selectedText}**`;
                        break;
                    case 'italic':
                        formattedText = `*${selectedText}*`;
                        break;
                    case 'heading':
                        formattedText = `## ${selectedText}`;
                        break;
                    case 'link':
                        formattedText = selectedText ? `[${selectedText}](url)` : '[texte du lien](url)';
                        break;
                    case 'image':
                        formattedText = `![${selectedText || 'alt text'}](url)`;
                        break;
                    case 'code':
                        formattedText = selectedText.includes('\n') ? 
                            '```\n' + selectedText + '\n```' : 
                            '`' + selectedText + '`';
                        break;
                    case 'quote':
                        formattedText = selectedText.split('\n').map(line => `> ${line}`).join('\n');
                        break;
                    case 'list-ul':
                        formattedText = selectedText ? 
                            selectedText.split('\n').map(line => `- ${line}`).join('\n') : 
                            '- élément de liste\n- élément de liste\n- élément de liste';
                        break;
                    case 'list-ol':
                        formattedText = selectedText ? 
                            selectedText.split('\n').map((line, i) => `${i+1}. ${line}`).join('\n') : 
                            '1. premier élément\n2. deuxième élément\n3. troisième élément';
                        break;
                }
                
                textarea.focus();
                document.execCommand('insertText', false, formattedText);
                
                // Mettre à jour la prévisualisation si elle est visible
                if (document.getElementById('preview-toggle')?.checked) {
                    updatePreview();
                }
            });
        });
    }
    
    // =======================================================
    // Auto-complétion des mentions
    // =======================================================
    function setupMentionAutocomplete() {
        const textarea = document.getElementById('id_content');
        if (!textarea) return;
        
        let mentionDropdown = document.createElement('div');
        mentionDropdown.className = 'mention-dropdown dropdown-menu';
        mentionDropdown.style.display = 'none';
        mentionDropdown.style.position = 'absolute';
        document.body.appendChild(mentionDropdown);
        
        // Liste d'utilisateurs suggérés (à remplacer par une requête AJAX en production)
        const suggestedUsers = window.FORUM_USERS || [];
        
        textarea.addEventListener('input', function(e) {
            const text = this.value;
            const pos = this.selectionStart;
            
            // Chercher le début de la mention potentielle
            let start = pos;
            while (start > 0 && text.charAt(start - 1) !== '@' && text.charAt(start - 1) !== ' ' && text.charAt(start - 1) !== '\n') {
                start--;
            }
            
            // Vérifier si on a trouvé une mention potentielle
            if (start > 0 && text.charAt(start - 1) === '@') {
                const query = text.substring(start, pos);
                
                // Si la requête est vide ou trop courte, masquer le dropdown
                if (query.length < 2) {
                    mentionDropdown.style.display = 'none';
                    return;
                }
                
                // Filtrer les suggestions
                const matches = suggestedUsers.filter(user => 
                    user.toLowerCase().includes(query.toLowerCase())
                ).slice(0, 5); // Limiter à 5 suggestions
                
                if (matches.length > 0) {
                    // Positionner le dropdown
                    const coords = getCaretCoordinates(this, pos);
                    const rect = this.getBoundingClientRect();
                    
                    mentionDropdown.style.top = (rect.top + coords.top + 20) + 'px';
                    mentionDropdown.style.left = (rect.left + coords.left) + 'px';
                    
                    // Remplir le dropdown
                    mentionDropdown.innerHTML = '';
                    matches.forEach(username => {
                        const item = document.createElement('a');
                        item.className = 'dropdown-item';
                        item.href = '#';
                        item.textContent = username;
                        
                        item.addEventListener('click', function(e) {
                            e.preventDefault();
                            
                            // Insérer le nom d'utilisateur
                            const newText = text.substring(0, start - 1) + '@' + username + ' ' + text.substring(pos);
                            textarea.value = newText;
                            
                            // Déplacer le curseur après le nom d'utilisateur
                            const newPos = start + username.length + 1;
                            textarea.setSelectionRange(newPos, newPos);
                            
                            // Masquer le dropdown
                            mentionDropdown.style.display = 'none';
                            
                            // Mettre à jour la prévisualisation
                            if (document.getElementById('preview-toggle')?.checked) {
                                updatePreview();
                            }
                        });
                        
                        mentionDropdown.appendChild(item);
                    });
                    
                    // Afficher le dropdown
                    mentionDropdown.style.display = 'block';
                } else {
                    mentionDropdown.style.display = 'none';
                }
            } else {
                mentionDropdown.style.display = 'none';
            }
        });
        
        // Masquer le dropdown lorsque le focus est perdu
        textarea.addEventListener('blur', function() {
            setTimeout(() => mentionDropdown.style.display = 'none', 200);
        });
    }
    
    // Helper pour obtenir les coordonnées du curseur dans un textarea
    function getCaretCoordinates(element, position) {
        // Créer un clone caché pour calculer la position
        const clone = document.createElement('div');
        clone.style.position = 'absolute';
        clone.style.top = '0';
        clone.style.left = '0';
        clone.style.visibility = 'hidden';
        clone.style.whiteSpace = 'pre-wrap';
        clone.style.wordWrap = 'break-word';
        clone.style.overflow = 'hidden';
        
        // Copier les propriétés de style pertinentes
        const styles = window.getComputedStyle(element);
        ['font-size', 'font-family', 'line-height', 'padding', 'border', 'box-sizing'].forEach(prop => {
            clone.style[prop] = styles[prop];
        });
        
        // Définir la largeur
        clone.style.width = element.offsetWidth + 'px';
        
        // Ajouter le texte jusqu'à la position du curseur
        const textBeforeCaret = element.value.substring(0, position);
        clone.textContent = textBeforeCaret;
        
        // Ajouter un élément span là où le curseur devrait être
        const span = document.createElement('span');
        span.textContent = '.';
        clone.appendChild(span);
        
        // Ajouter au document et obtenir la position
        document.body.appendChild(clone);
        const rect = span.getBoundingClientRect();
        const result = {
            top: rect.top - clone.getBoundingClientRect().top,
            left: rect.left - clone.getBoundingClientRect().left
        };
        
        // Nettoyer
        document.body.removeChild(clone);
        
        return result;
    }
    
    // =======================================================
    // Initialisation
    // =======================================================
    // Initialiser les réactions
    setupReactions();
    
    // Initialiser les boutons de citation
    setupQuoteButtons();
    
    // Mettre en évidence les mentions
    highlightMentions();
    
    // Initialiser la prévisualisation Markdown
    setupMarkdownPreview();
    
    // Initialiser les boutons de formatage Markdown
    setupMarkdownButtons();
    
    // Initialiser l'auto-complétion des mentions
    setupMentionAutocomplete();
});