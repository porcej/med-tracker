// var socket = io();
var socket = io.connect('//' + document.domain + ':8083' + '/chat');

var currentRoom = localStorage.getItem('currentRoom') || 'Medical';

socket.on('connect', function() {
    joinRoom(currentRoom);
});

socket.on('previous_messages', function(messages) {
    let chatBox = document.getElementById('chat-box');
    chatBox.innerHTML = '';
    messages.forEach(function(message) {
        addMessageToChatBox(message, message.assignment === assignment ? 'right' : 'left');
    });
});

socket.on('receive_message', function(data) {
    addMessageToChatBox(data, data.assignment === assignment ? 'right' : 'left');
});

document.getElementById('message-form').onsubmit = function(e) {
    e.preventDefault();
    let message = document.getElementById('message').value;
    let assignment = document.getElementById('assignment').value;
    let username = document.getElementById('username').value;
    if (message) {
        socket.emit('send_message_public', {message: message, room: currentRoom, assignment: assignment, username: username});
        document.getElementById('message').value = '';
    }
};

document.getElementById('room-select').onchange = function() {
    let newRoom = this.value;
    if (newRoom !== currentRoom) {
        leaveRoom(currentRoom);
        currentRoom = newRoom;
        localStorage.setItem('currentRoom', currentRoom); // Update room in localStorage
        joinRoom(currentRoom);
    }
};

function joinRoom(room) {
    socket.emit('join', {room: room});
}

function leaveRoom(room) {
    socket.emit('leave', {room: room});
}

function addMessageToChatBox(data, alignment) {
    let chatBox = document.getElementById('chat-box');
    let messageDiv = document.createElement('div');
    messageDiv.classList.add('message', alignment);

    // Format the timestamp to show only hours and minutes
    let timestamp = new Date(data.created_at);
    let hours = timestamp.getHours().toString().padStart(2, '0');
    let minutes = timestamp.getMinutes().toString().padStart(2, '0');
    let formattedTime = `${hours}:${minutes}`;

    let bubble = document.createElement('div');
    bubble.classList.add('bubble', alignment === 'right' ? 'right' : 'left');
    bubble.innerHTML = `<strong>${data.assignment}</strong> (${data.username})<span class="timestamp">  @  ${formattedTime}</span><br>${data.content}`;

    messageDiv.appendChild(bubble);
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}