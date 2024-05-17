'use strict'

document.addEventListener('DOMContentLoaded', function () {

  // Displays the element by removing the "hidden" class.
  function displayEl (el) {
    document.querySelector(el).classList.remove('hidden')
  }

  // Copied from https://stackoverflow.com/questions/5639346.
  function cookie (name) {
    const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
    return match ? match.pop() : ''
  }

  // Remove "no-js" class from element, if it exists
  document.documentElement.classList.remove('no-js')
  document.documentElement.classList.add('js')

  //
  // Tabbed description lists (<dl>)
  //
  document.querySelectorAll('dl.tabbed').forEach(dl => {
    const dts = dl.querySelectorAll('dt')
    const dds = dl.querySelectorAll('dd')

    const switchTab = (dt) => {
      dts.forEach(el => el.classList.remove('selected'))
      dds.forEach(el => el.classList.add('screen-hidden'))
      dt.classList.add('selected')
      dt.nextElementSibling.classList.remove('screen-hidden')
    }
    switchTab(dts[0])

    dts.forEach(el => {
      el.tabIndex = 0
      el.addEventListener('click', (ev) => switchTab(ev.target))
      el.addEventListener('keydown', (ev) => {
        if (ev.keyCode === 13) {  // <Enter>
          switchTab(ev.target)
        }
      })
    })
  })

  //
  // Open all <details> in <main> for print.
  //
  // Note: This currently cannot be done using CSS only,
  // see https://github.com/w3c/csswg-drafts/issues/2084.
  //
  // Note: Approach with a listener on MediaQueryList doesn't work here,
  // see https://bugzilla.mozilla.org/show_bug.cgi?id=774398.
  //
  window.addEventListener('beforeprint', () => {
    document.querySelectorAll('main details').forEach(el => {
      el.open = true
    })
  })

  //
  // Functionality of navigation expanders
  //
  document.querySelectorAll('.site-nav .expander').forEach(el => {
    el.addEventListener('click', function () {
      this.parentElement.classList.toggle('collapsed')
    })
  })

  //
  // Display a list of available archived versions (semesters)
  //
  const currentPath = decodeURIComponent(window.location.pathname).split('/')
  const branchesPath = ['', currentPath[1], '.branches.json'].join('/')

  const req = new XMLHttpRequest()
  req.open('GET', branchesPath, true)
  req.onload = () => {
    if (req.status >= 200 && req.status < 400) {
      const branches = JSON.parse(req.responseText)

      if (branches.length === 0) {
        // Don't display the semester selector if there are no branches.
        return
      }
      const semestersHTML = branches.map(function (item) {
        return '<li><a href="' + item.url + '">' + item.branch + '</a></li>'
      }).join('\n')

      // Display the semester selector
      document.querySelector('#semesters').innerHTML = semestersHTML
      displayEl('.course-semester')

      const currentBranch = currentPath[2].charAt(0) === '@' ? currentPath[2].slice(1) : null

      // Display a note when looking on older version than the current one.
      if (currentBranch && currentBranch !== 'master') {
        const isHistoryBranch = branches.some(item => item.branch === currentBranch)
        displayEl('#version-msg')
        displayEl(isHistoryBranch ? '#version-msg-history-icon' : '#version-msg-other-icon')
        document.querySelector('#version-msg-branch').innerHTML = currentBranch
      }
    }
  }
  req.send()

  //
  // User bar and logout button
  //

  // Retrieve and display user information from cookies.
  document.querySelector('#username').innerText = cookie('oauth_username')

  // Display the userbar when the user is logged in, otherwise display the login link.
  displayEl(cookie('oauth_access_token') ? '#userbar' : '#login-link')
})
