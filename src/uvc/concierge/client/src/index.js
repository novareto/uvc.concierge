import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';
import './index.css';

import 'bootstrap/dist/css/bootstrap.css';
import 'bootstrap/dist/css/bootstrap-theme.css';


var div = document.createElement('div');
div.setAttribute('id', 'container');
document.body.prepend(div);

ReactDOM.render(
  <App />,
  document.getElementById('container')
);