function register() {
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    fetch('https://abhigyan.pythonanywhere.com/register', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            "username": username,
            "password": password
        })
    })
    .then(function(response) {
        if (!response.ok) {
            throw Error(response.statusText);
        }
        fetch('https://abhigyan.pythonanywhere.com/add_city', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
            "city_name": "Kolkata"
        })
        })
        window.location.href = 'index.html'
    })
    
    .catch(function(error) {
        // Handle errors
        console.log(error);
    });
}

function login(username, password) {
    console.log(username)
        fetch(`https://abhigyan.pythonanywhere.com/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        })
        .then(function(response) {
            console.log('Response status:', response.status);
            console.log('Response body:', response.json());
    
            if (!response.ok) {
                throw Error(response.statusText);
            }
            return response.json();
        })
        .then(function(data) {
            // Redirect to home page on successful login
            console.log("success")
            accessToken = data.access_token;
            localStorage.setItem('accessToken', accessToken);
            window.location.href = 'home.html';
        })
        .catch(function(error) {
            // Display error message
            console.log("failure")
            document.getElementById('error').innerText = 'Invalid username or password';
        });
}
