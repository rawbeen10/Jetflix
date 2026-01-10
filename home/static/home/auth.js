// Auth UI JavaScript - Jetflix Design System
class JetflixAuth {
    constructor() {
        this.currentTab = 'login';
        this.forms = {
            login: document.getElementById('loginForm'),
            signup: document.getElementById('signupForm')
        };
        this.submitButtons = {
            login: document.getElementById('loginSubmit'),
            signup: document.getElementById('signupSubmit')
        };
        
        this.init();
    }
    
    init() {
        this.setupTabs();
        this.setupPasswordToggles();
        this.setupFormValidation();
        this.setupFormSubmission();
        this.setupKeyboardNavigation();
    }
    
    setupTabs() {
        const tabs = document.querySelectorAll('.auth-tab');
        const forms = document.querySelectorAll('.auth-form');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                const tabType = tab.dataset.tab;
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                tab.classList.add('active');
                
                // Update active form
                forms.forEach(f => f.classList.remove('active'));
                document.getElementById(tabType + 'Form').classList.add('active');
                
                this.currentTab = tabType;
                this.clearMessages();
                this.resetValidation();
            });
        });
    }
    
    setupPasswordToggles() {
        const toggles = document.querySelectorAll('.password-toggle');
        
        toggles.forEach(toggle => {
            toggle.addEventListener('click', () => {
                const targetId = toggle.dataset.target;
                const input = document.getElementById(targetId);
                const eyeOpen = toggle.querySelector('.eye-open');
                const eyeClosed = toggle.querySelector('.eye-closed');
                
                if (input.type === 'password') {
                    input.type = 'text';
                    eyeOpen.style.display = 'none';
                    eyeClosed.style.display = 'block';
                } else {
                    input.type = 'password';
                    eyeOpen.style.display = 'block';
                    eyeClosed.style.display = 'none';
                }
            });
        });
    }
    
    setupFormValidation() {
        // Login form validation
        const loginUsername = document.getElementById('loginUsername');
        const loginPassword = document.getElementById('loginPassword');
        
        loginUsername.addEventListener('input', () => this.validateLoginForm());
        loginPassword.addEventListener('input', () => this.validateLoginForm());
        
        // Signup form validation
        const signupUsername = document.getElementById('signupUsername');
        const signupEmail = document.getElementById('signupEmail');
        const signupPassword1 = document.getElementById('signupPassword1');
        const signupPassword2 = document.getElementById('signupPassword2');
        
        signupUsername.addEventListener('input', () => this.validateSignupForm());
        signupUsername.addEventListener('blur', () => this.validateUsername(signupUsername, 'signupUsernameError'));
        
        signupEmail.addEventListener('input', () => this.validateSignupForm());
        signupEmail.addEventListener('blur', () => this.validateEmail(signupEmail, 'signupEmailError'));
        
        signupPassword1.addEventListener('input', () => this.validateSignupForm());
        signupPassword1.addEventListener('blur', () => this.validatePassword(signupPassword1, 'signupPassword1Error'));
        
        signupPassword2.addEventListener('input', () => this.validateSignupForm());
        signupPassword2.addEventListener('blur', () => this.validatePasswordMatch(signupPassword1, signupPassword2, 'signupPassword2Error'));
    }
    
    validateLoginForm() {
        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        
        const isValid = username.length > 0 && password.length > 0;
        this.submitButtons.login.disabled = !isValid;
        
        return isValid;
    }
    
    validateSignupForm() {
        const username = document.getElementById('signupUsername').value.trim();
        const email = document.getElementById('signupEmail').value.trim();
        const password1 = document.getElementById('signupPassword1').value;
        const password2 = document.getElementById('signupPassword2').value;
        
        const isValid = username.length >= 3 && 
                       this.isValidEmail(email) && 
                       this.isValidPassword(password1) && 
                       password1 === password2;
        
        this.submitButtons.signup.disabled = !isValid;
        
        return isValid;
    }
    
    validateUsername(input, errorId) {
        const username = input.value.trim();
        const errorEl = document.getElementById(errorId);
        
        if (username.length === 0) {
            this.clearError(input, errorEl);
            return true;
        }
        
        if (username.length < 3) {
            this.showError(input, errorEl, 'Username must be at least 3 characters');
            return false;
        }
        
        if (!/^[a-zA-Z0-9_]+$/.test(username)) {
            this.showError(input, errorEl, 'Username can only contain letters, numbers, and underscores');
            return false;
        }
        
        this.clearError(input, errorEl);
        return true;
    }
    
    validateEmail(input, errorId) {
        const email = input.value.trim();
        const errorEl = document.getElementById(errorId);
        
        if (email.length === 0) {
            this.clearError(input, errorEl);
            return true;
        }
        
        if (!this.isValidEmail(email)) {
            this.showError(input, errorEl, 'Please enter a valid email address');
            return false;
        }
        
        this.clearError(input, errorEl);
        return true;
    }
    
    validatePassword(input, errorId) {
        const password = input.value;
        const errorEl = document.getElementById(errorId);
        
        if (password.length === 0) {
            this.clearError(input, errorEl);
            return true;
        }
        
        if (!this.isValidPassword(password)) {
            this.showError(input, errorEl, 'Password must be at least 8 characters with uppercase, lowercase, and number');
            return false;
        }
        
        this.clearError(input, errorEl);
        return true;
    }
    
    validatePasswordMatch(password1Input, password2Input, errorId) {
        const password1 = password1Input.value;
        const password2 = password2Input.value;
        const errorEl = document.getElementById(errorId);
        
        if (password2.length === 0) {
            this.clearError(password2Input, errorEl);
            return true;
        }
        
        if (password1 !== password2) {
            this.showError(password2Input, errorEl, 'Passwords do not match');
            return false;
        }
        
        this.clearError(password2Input, errorEl);
        return true;
    }
    
    isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }
    
    isValidPassword(password) {
        return password.length >= 8 && 
               /(?=.*[a-z])/.test(password) && 
               /(?=.*[A-Z])/.test(password) && 
               /(?=.*\d)/.test(password);
    }
    
    showError(input, errorEl, message) {
        input.classList.add('error');
        errorEl.textContent = message;
        errorEl.classList.add('show');
    }
    
    clearError(input, errorEl) {
        input.classList.remove('error');
        errorEl.classList.remove('show');
    }
    
    resetValidation() {
        const inputs = document.querySelectorAll('.form-group input');
        const errors = document.querySelectorAll('.form-error');
        
        inputs.forEach(input => input.classList.remove('error'));
        errors.forEach(error => error.classList.remove('show'));
        
        this.submitButtons.login.disabled = true;
        this.submitButtons.signup.disabled = true;
    }
    
    setupFormSubmission() {
        this.forms.login.addEventListener('submit', (e) => this.handleSubmit(e, 'login'));
        this.forms.signup.addEventListener('submit', (e) => this.handleSubmit(e, 'signup'));
    }
    
    async handleSubmit(e, formType) {
        e.preventDefault();
        
        const submitBtn = this.submitButtons[formType];
        const submitText = submitBtn.querySelector('.submit-text');
        const submitLoader = submitBtn.querySelector('.submit-loader');
        
        // Show loading state
        submitBtn.disabled = true;
        submitText.style.opacity = '0';
        submitLoader.style.display = 'block';
        
        try {
            // For now, just submit the form normally after showing loading
            setTimeout(() => {
                this.forms[formType].submit();
            }, 800);
            
        } catch (error) {
            console.error('Form submission error:', error);
            this.showMessage('Network error. Please check your connection.', 'error');
            
            // Reset loading state
            submitBtn.disabled = false;
            submitText.style.opacity = '1';
            submitLoader.style.display = 'none';
        }
    }
    
    showMessage(text, type) {
        const messagesContainer = document.getElementById('authMessages');
        
        const messageEl = document.createElement('div');
        messageEl.className = `auth-message ${type}`;
        messageEl.textContent = text;
        
        messagesContainer.appendChild(messageEl);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (messageEl.parentNode) {
                messageEl.remove();
            }
        }, 5000);
    }
    
    clearMessages() {
        const messagesContainer = document.getElementById('authMessages');
        messagesContainer.innerHTML = '';
    }
    
    setupKeyboardNavigation() {
        document.addEventListener('keydown', (e) => {
            // Tab navigation between forms
            if (e.key === 'Tab' && e.ctrlKey) {
                e.preventDefault();
                const currentTabEl = document.querySelector('.auth-tab.active');
                const nextTab = this.currentTab === 'login' ? 'signup' : 'login';
                const nextTabEl = document.querySelector(`[data-tab="${nextTab}"]`);
                nextTabEl.click();
            }
            
            // Enter to submit
            if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
                const form = e.target.closest('form');
                const submitBtn = form.querySelector('.auth-submit');
                if (!submitBtn.disabled) {
                    submitBtn.click();
                }
            }
        });
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new JetflixAuth();
});