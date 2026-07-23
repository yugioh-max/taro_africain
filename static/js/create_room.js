const checkbox = document.getElementById('is_private')
const passwordField = document.getElementById('password-field')

checkbox.addEventListener('change', function(){
    passwordField.style.display = this.checked ? 'block' : 'none';
});