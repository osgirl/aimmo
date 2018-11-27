import styled from 'styled-components'
import React, { Component } from 'react'
import PropTypes from 'prop-types'
import { IconButton, Typography } from '@material-ui/core'
import CodeHintsIcon from 'components/icons/CodeHints'

export const Layout = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`

export default class DrawerIconButton extends Component {
  render () {
    return (
      <Layout>
        <IconButton>
          <CodeHintsIcon />
        </IconButton>
        <Typography variant='caption'>
        Code Hints
        </Typography>
      </Layout>
    )
  }
}
