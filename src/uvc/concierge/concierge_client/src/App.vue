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
              <button v-on:click.prevent="handleLogin" class="button is-primary"> Login </button>
            </div>
          </a>
        </div>
      </div>

    </nav>
  </div>
</template>

<script>

export default {
  name: 'app',
  data() {
    return {
      loggedIn: false,
      isConnected: false,
      socketMessage: '',
      logindata: {
        login: '',
        password: ''
      }
    }
  },
  methods: {
    handleLogin() {
      console.log('DRINNN')
      if (this.logindata.login == '0101010001'){
        this.loggedIn = true
      }
    },
    logout() {
       this.loggedIn = false
       this.logindata.login = ""
       this.logindata.password = ""
    }
  },
}
</script>

<style lang="scss" scoped>
@import './node_modules/bulma/bulma.sass';
</style>
