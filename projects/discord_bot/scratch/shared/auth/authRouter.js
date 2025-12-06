const express = require('express');
const { register, login, refresh } = require('./userController');
const router = express.Router();

router.post('/register', register);
router.post('/login', login);
router.post('/refresh', refresh);

module.exports = router;
