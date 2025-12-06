"use strict";

const topFn = require('./bonusStore').top;
const router = require('./bonusRouter');

module.exports = {
  top: topFn,
  router
};
