const express = require('express');
const cors = require('cors');
const path = require('path');
const app = express();

const dist = path.join(__dirname, 'dist');
app.use(cors());
app.use('/', express.static(dist));

app.get('/', function(req,res) {
    res.sendFile(path.join(dist, 'index.html'));
});

app.listen(3000);