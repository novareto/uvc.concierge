import Vue from 'vue'
import App from './App.vue'

document.onreadystatechange = () => {
  console.log('LOS GEHT ES!')
  new Vue({
    el: '#app',
    render: h => h(App),
  },
  )
}
