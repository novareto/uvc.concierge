import Vue from 'vue'
import App from './App.vue'
import Socket from './socket'


document.onreadystatechange = () => {
  new Vue({
    el: '#app',
    render: h => h(App),
  },
  )
}
