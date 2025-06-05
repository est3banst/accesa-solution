import { useState } from 'react'
import Inicio from './components/Inicio'


function App() {
  const [count, setCount] = useState(0)

  return (
    <>
    <Inicio/>
    </>
  )
}

export default App
