<template>
  <div id="concierge">

    <nav class="navbar is-info is-transparent" role="navigation" aria-label="main navigation">

      <div class="navbar-brand">
        <a class="navbar-item">
          Concierge
        </a>
      </div>

      <div class="navbar-menu">
        <div class="navbar-start">
          <a class="navbar-item">
            MENUS
          </a>
        </div>

        <div class="navbar-end">

          <div class="navbar-item has-dropdown is-hoverable is-right" v-if="loggedIn">

            <a class="navbar-link">
              <span class="icon">
                <i class="fa fa-home"></i>
              </span>
                <span v-html="logindata.login"> </span>
            </a>

            <div class="navbar-dropdown is-right">
              <a v-on:click.prevent="logout" class="navbar-item">
                Logout
              </a>
            </div>
          </div>

          <a class="navbar-item" v-if="!loggedIn">
            <div class="field is-horizontal">
              <div class="control">
                <input v-model="logindata.login" class="input" type="text" placeholder="Mitgliedsnummer / Email">
              </div>
              <div class="control">
                <input v-model="logindata.password" class="input" type="password" placeholder="Passwort">
              </div>
              <button v-on:click.prevent="submit" class="button is-primary"> Login </button>
            </div>
          </a>
        </div>
      </div>

    </nav>
  </div>
</template>

<script>

import Socket from "./socket"

export default {
  name: 'app',
  created() {
    Socket.$on("message", this.receive);
    Socket.$on("error", this.fail);
  },
  beforeDestroy() {
    Socket.$off("message", this.receive)
  },
  data() {
    return {
      loggedIn: false,
      socketMessage: '',
      logindata: {
        login: '',
        password: ''
      }
    }
  },
  methods: {
    receive(msg) {
      var payload = JSON.parse(msg);
      console.log('THIS IS MY PAYLOAD', payload)
      if (payload.length != 2) {
	alert('Malformed response');
      }
      if (payload[0] == 'login_success') {
	payload[1].data.forEach(function(entry) {
	    if (entry[0] == 'Set-Cookie') {
	      document.cookie = entry[1];
	      alert("Logged in");
	      this.loggedIn = true;
	    }
	  });
      }
      else if (payload[0] == 'login_error') {
	this.error = 'Login failed : ' + payload[1]['message'];
      }
      else if (payload[0] == 'login_failure') {
	this.error = 'Login failed';
      }
      else {
	console.log(msg);
      }
    },
    fail(msg) {
      this.error = msg;
    },
    submit() {
      var credentials = {
        login: this.logindata.login,
        password: this.logindata.password
      }
      var command = JSON.stringify(["login", credentials]);
      Socket.send(command);
      alert(command);
    }
  },
}
</script>

<style lang="scss" scoped>
@import './node_modules/bulma/bulma.sass';
</style>
