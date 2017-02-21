import React, { Component } from 'react';
import './App.css';
import { Navbar, Nav, NavItem, FormGroup, Button, FormControl, NavDropdown, MenuItem } from 'react-bootstrap';


function waitForSocketConnection(socket, callback){
    setTimeout(
        function () {
            if (socket.readyState === 1) {
                console.log("Connection is made")
                if(callback != null){
                    callback();
                }
                return;

            } else {
                console.log("wait for connection...")
                waitForSocketConnection(socket, callback);
            }

        }, 5); // wait 5 milisecond for the connection...
}


class LoginComponent extends React.Component {

  constructor(props) {
    super(props);
    console.log(props)
    this.socket = props.conn;
    var ws = this.socket;
    this.handleSubmit = this.handleSubmit.bind(this);
    waitForSocketConnection(ws, function() {
       ws.send(JSON.stringify(['isloggedin', '']));
    })  
  }



  handleSubmit(event) {
    this.setState({login: event.target.login.value})
    var data = {login:event.target.login.value, password:event.target.password.value};
    this.socket.send(JSON.stringify(["login", data]));
    event.preventDefault();
  }

  render() {
    const isLoggedIn = this.props.loggedIn;
    let elem = null;
    if (!isLoggedIn) {
      elem = <form onSubmit={this.handleSubmit}>
        <Navbar.Form pullRight >
          <FormGroup>
            <FormControl type="text" placeholder="Username" name="login" />
            {' '}
            <FormControl type="text" placeholder="Pasword" name="password" />
            {' '}
          </FormGroup>
          {' '}
          <Button type="submit">Submit</Button>
        </Navbar.Form>
      </form>
    }
    else {
      elem = 
      <Nav pullRight>
        <NavDropdown pullRight title="ck@novareto.de" id="basic-nav-dropdown">
           <MenuItem eventKey={3.1}>Logout</MenuItem>
        </NavDropdown>
        </Nav>
    }
    return (elem)
  }
}
  
class BasicMenus extends Component {
  
  constructor(props) {
    super(props)
    this.conn = props.conn
    this.handle_redirect = this.handle_redirect.bind(this);
    this.conn.onmessage = (e) => {
      console.log(e);
      var response = JSON.parse(e.data);
      if (response.length !== 2) {
        alert('Malformed response');
      }
      else {
        if (response[0] === 'login_success' || response[0] === 'already_logged_in') {
          if (response[0] === 'login_success') {
            response[1].data.forEach(function (entry) {
              if (entry[0] === 'Set-Cookie') {
                document.cookie = entry[1];
              }
            });
          }
          var menus = [];
          response[1].menu.forEach((menu) => {
            menus.push(
              { title: menu[1], href: menu[0] }
            )
            this.setState({menus: menus})
            this.setState({loggedIn: true})
          }
          );
        };
        
      }
    }
  
}
  componentWillMount(){
    this.setState({menus: []})
  }
  
  handle_redirect(event) {
    return window.location=event.target.href;
  }
  
  render() {
    return (
    <Navbar.Collapse>
      <Nav>
        {
          this.state.menus.map( (menu) => {
            return <NavItem onClick={this.handle_redirect} href={menu.href}>{menu.title}</NavItem>
          })
        }
      </Nav>
       <LoginComponent conn={this.conn} loggedIn={this.state.loggedIn}> </LoginComponent>
    </Navbar.Collapse>
    )
  }
}

var socket = new WebSocket("ws://karl.novareto.de:8080/socket");


class App extends Component {
  
  render() {
    return (
      <div className="App">
        <Navbar inverse collapseOnSelect>
          <Navbar.Header>
            <Navbar.Brand>
              <a href=""> UVC.Concierge </a>
            </Navbar.Brand>
             <Navbar.Toggle />
          </Navbar.Header>
          <BasicMenus conn={socket}> </BasicMenus>
        </Navbar>
      </div>
    )
  }
}

export default App;
