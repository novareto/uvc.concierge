import React, { Component } from 'react';
import './App.css';
import { Navbar, Nav, NavItem, FormGroup, Button, FormControl, NavDropdown, MenuItem } from 'react-bootstrap';
import { AlertList } from "react-bs-notifier";


function delete_cookie(name, domain) {
  document.cookie = name +'=; Path=/; Domain='+ domain +'; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
}


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
    this.logout = this.logout.bind(this);
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

  logout(event) {
     console.log('LOGOUT');
    this.socket.send(JSON.stringify(["logout", '']));
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
           <MenuItem onClick={this.logout} eventKey={3.1}>Logout</MenuItem>
        </NavDropdown>
        </Nav>
    }
    return (elem)
  }
}


class BasicMenus extends Component {

    onAlertDismissed(alert) {
        const alerts = this.state.alerts;

	// find the index of the alert that was dismissed                                                                                                                       
        const idx = alerts.indexOf(alert);

        if (idx >= 0) {
            this.setState({
                // remove the alert from the array                                                                                                                              
                alerts: [...alerts.slice(0, idx), ...alerts.slice(idx + 1)]
            });
	}
  }

  generate(type, message) {
    const newAlert = {
       id: (new Date()).getTime(),
       type: type,
       headline: `Whoa, ${type}!`,
       message: message
    };
    console.log(this);
    this.setState({
      alerts: [...this.state.alerts, newAlert]
    });
  }

  
  constructor(props) {
    super(props)

    this.state = {
        position: "top-right",
        alerts: [],
        timeout: 3000,
    };

    this.conn = props.conn
    this.handle_redirect = this.handle_redirect.bind(this);
    this.conn.onmessage = (e) => {
      var response = JSON.parse(e.data);
      if (response.length !== 2) {
        alert(response);
      }
      else {
        if (response[0] === 'login_success' || response[0] === 'already_logged_in') {
          if (response[0] === 'login_success') {
            this.generate('success', 'You logged in successfully.');
            response[1].data.forEach((entry) => {
              if (entry[0] === 'Set-Cookie') {
                  console.log(entry[1]);
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
        } else if (response[0] === 'logged_out') {
	    response[1].domains.forEach((entry) => {
		delete_cookie(entry[0], entry[1]);
	    })
	    this.setState({menus: []});
            this.setState({loggedIn: false});
	    this.generate('success', 'You are now logged out.');
	}
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
<div>
        <AlertList
            position={this.state.position}
            alerts={this.state.alerts}
            timeout={this.state.timeout}
            dismissTitle="Begone!"
            onDismiss={this.onAlertDismissed.bind(this)}
            />
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
</div>
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
