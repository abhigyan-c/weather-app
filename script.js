document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault();

    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
    var accessToken;
    console.log(username)
    console.log(password)

    fetch('https://abhigyan.pythonanywhere.com/login', {
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
        // console.log('Response status:', response.status);
        // console.log('Response body:', response.json());

        if (!response.ok) {
            throw Error(response.statusText);
        }
        return response.json();
    })
    .then(function(data) {
        // Redirect to home page on successful login
        if(data.message !== 'Invalid username or password') {
            accessToken = data.access_token;
            localStorage.setItem('accessToken', accessToken);
            window.location.href = 'home.html';
        }
        else
            throw Error()
    })
    .catch(function(error) {
        // Display error message
        console.log("failure")
        document.getElementById('error').innerText = 'Invalid username or password';
    });
});

