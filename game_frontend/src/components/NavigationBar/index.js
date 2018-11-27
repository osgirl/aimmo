import React, { Component } from 'react'
import styled from 'styled-components'
import AppBar from '@material-ui/core/AppBar'
import Toolbar from '@material-ui/core/Toolbar'
import IconButton from '@material-ui/core/IconButton'
import CloseIcon from 'components/icons/Close'
import Drawer from '@material-ui/core/Drawer'
import CodeHintsIcon from 'components/icons/CodeHints'
import { List, ListItem, ListItemIcon, ListItemText, Button } from '@material-ui/core'
import MenuIcon from 'components/icons/Menu'
import DrawerIconButton from 'components/DrawerIconButton'

export const NavigationBarLayout = styled.nav`
    grid-area: navigation-bar;
`

export const CloseToolbar = styled(Toolbar)`
  justify-content: flex-end;
`

export const SideList = styled(List)`
  display: flex;
  justify-content: space-around;
  flex-direction: column;
  flex-grow: 2;
`

export const ListLayout = styled.nav`
  display: flex;
  flex-direction: column;
  height: 100%;
`

export const MyAppBar = styled(AppBar)`
  && {
    ${props => console.log(props.theme.zIndex)}
    z-index: ${props => props.theme.zIndex.modal + 1};
  }
`

export const ToolbarPadder = styled.div`
  ${props => props.theme.mixins.toolbar}
`

class MyList extends Component {
  render () {
    return (
      <ListLayout>
        <ToolbarPadder />
        <SideList>
          <ListItem>
            <DrawerIconButton />
            {/* <ListItemText primary='Code Hints' /> */}
          </ListItem>
          <ListItem>
            <DrawerIconButton />
            {/* <ListItemText primary='Code Hints' /> */}
          </ListItem>
          <ListItem>
            <DrawerIconButton />
            {/* <ListItemText primary='Code Hints' /> */}
          </ListItem>
          <ListItem>
            <DrawerIconButton />
            {/* <ListItemText primary='Code Hints' /> */}
          </ListItem>
        </SideList>
      </ListLayout>
    )
  }
}

export default class NavigationBar extends Component {
  state = {
    drawerOpen: true
  }

  toggleDrawer = () => {
    console.log('got here')
    console.log(`setting drawer to ${!this.state.drawerOpen}`)
    this.setState({
      drawerOpen: !this.state.drawerOpen
    })
  }

  render () {
    return (
      <NavigationBarLayout>
        <MyAppBar

          color='secondary'
          position='sticky'>
          <CloseToolbar>
            <Button
              variant='fab'
              onClick={this.toggleDrawer}
            >
              <MenuIcon />
            </Button>
            {/* <IconButton
              // href='/aimmo'
              aria-label='Close'
              color='inherit'>
              <MenuIcon />
            </IconButton> */}

          </CloseToolbar>
        </MyAppBar>
        <Drawer
          anchor='right'
          open={this.state.drawerOpen}
          onClose={this.toggleDrawer}
          ModalProps={{ hideBackdrop: true }}
        >
          <MyList />
        </Drawer>
      </NavigationBarLayout>
    )
  }
}
