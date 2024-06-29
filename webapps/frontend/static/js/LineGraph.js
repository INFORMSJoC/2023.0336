class LineGraph {
  constructor(options) {

    this.dimensions = options.dimensionsIn;
    this.dimensions.ctrWidth = this.dimensions.width - this.dimensions.margin.left - this.dimensions.margin.right
    this.dimensions.ctrHeight = this.dimensions.height - this.dimensions.margin.top - this.dimensions.margin.bottom
    this.numXTicks = options.numXTicks;
    this.id = options.elId;
    this.xLabelStr = options.xLabelStr
    this.xFieldStr = options.xFieldStr
    this.yLabelStr = options.yLabelStr
    this.yFieldStr = options.yFieldStr  
    this.legendColors = options.legendColors;
    this.validLegendEntries = options.legends

    // will be created on first setData call to render and updated on subsequent calls
    this.svg_graph;
    this.svg_graph_ctr;
    this.xAxis;
    this.xAxisGroup;
    this.xAxisLabel;
    this.xAxisGroupTickLabels;
    this.yAxis;
    this.yAxisGroup;
    this.yAxisLabel;
    this.legendEntries;
  }

  setData(datasetIn, hasDates, hasCategories) {    
    this.dataset = []
    
    // Set the ranges
    if (hasDates) {
      this.xScale = d3.scaleTime().range([0, this.dimensions.ctrWidth])
      this.xAccessor = (d) => d.startDate;
      this.yAccessor = (d) => +d.value;
      // Scale the range of the data
      this.xScale.domain(d3.extent(datasetIn, this.xAccessor));    
    }
    else {
      var timeAccessor =  (d) => d['time'];
      this.xScale = d3.scaleLinear()
        .domain(d3.extent(datasetIn, timeAccessor))
        .rangeRound([0, this.dimensions.ctrWidth]);
      this.xAccessor = (d) => d.time;
      this.yAccessor = (d) => +d.power;       
    }

    this.yScale = d3.scaleLinear().range([this.dimensions.ctrHeight, 0]);
    
    let dataNest = Array.from(
      d3.group(datasetIn, d => hasCategories ? d.category : "Powerload"), 
      ([key, value]) => ({key, value})
    )

    let validKeys = Object.keys(this.validLegendEntries);
    let validData = [];

    dataNest.forEach(entry => {            
      if (validKeys.includes(entry.key)){
        this.dataset.push(entry)
        validData = validData.concat(entry.value)
      }
    })

    this.yScale.domain(d3.extent(validData, this.yAccessor));  

    // Define the Axes
    let xTicks = this.numXTicks ? this.numXTicks : Math.floor(this.dimensions.width/100);
    let yTicks = Math.floor(this.dimensions.height/100)
    this.xAxis = d3.axisBottom(this.xScale)
      .ticks(xTicks)

    this.yAxis = d3.axisLeft(this.yScale)
      .ticks(yTicks)

    // Define the line
    if (hasDates) {
      this.xAxis.tickFormat(d3.timeFormat('%d-%b'));  // append -%y to add the year
      this.valueline = d3.line()	
      .x((d) => this.xScale(d.startDate))
      .y((d) => this.yScale(d.value));
    }

    else {
      this.valueline = d3.line()	
      .x((d) => this.xScale(d.time))
      .y((d) => this.yScale(d.power));
    }

    this.render()            
  }

  render() {
    // Gridline - see also: https://stackoverflow.com/questions/15580300/proper-way-to-draw-gridlines
    // Draw Image
    if (this.svg_graph) {
      this.svg_graph.remove()
      this.svg_graph_ctr.remove()
    }

    this.svg_graph = d3.select(this.id)
      .append('svg')
      .attr('width', this.dimensions.width)
      .attr('height', this.dimensions.height)

    this.svg_graph_ctr = this.svg_graph.append('g')
      .attr('transform',
        `translate(${this.dimensions.margin.left}, ${this.dimensions.margin.top})`
      )
                
    // Add the axes
    this.yAxisGroup = this.svg_graph_ctr.append('g')
      .call(this.yAxis)
      .classed('axis', true)

    this.yAxisLabel = this.yAxisGroup.append('text')
      .attr('x', -this.dimensions.ctrHeight / 2)
      .attr('y', -this.dimensions.margin.left + 15)
      .attr('fill', 'black')
      .style('transform', 'rotate(270deg)')
      .style('text-anchor', 'middle')

    this.xAxisGroup = this.svg_graph_ctr.append('g')
      .call(this.xAxis)
      .classed('axis', true)
      .style('transform', `translateY(${this.dimensions.ctrHeight}px)`)

    this.xAxisLabel = this.xAxisGroup.append('text')
      .attr('x', this.dimensions.ctrWidth / 2)
      .attr('y', this.dimensions.margin.bottom - 20)
      .attr('fill', 'black')

    this.xAxisGroupTickLabels = this.xAxisLabel.selectAll("text")
      .style("text-anchor", "end")
      .style('font-size', "18px")
      .attr("dx", "-.8em")
      .attr("dy", ".15em")
      .attr("transform", "rotate(-65)");

    this.yAxisLabel.html(this.yLabelStr)
    this.xAxisLabel.html(this.xLabelStr)                

    var verticalGridlines = d3.axisBottom()
    .tickFormat("")
    .ticks(5)
    .tickSize(this.dimensions.ctrHeight)
    .scale(this.xScale);

    var horizontalGridlines = d3.axisRight()
      .tickFormat("")
      .ticks(5)
      .tickSize(this.dimensions.ctrWidth)
      .scale(this.yScale);

    this.svg_graph_ctr.append("g")
      .attr("class", "grid")
      .call(verticalGridlines)
      .append('g')
      .attr("class", "grid")
      .call(horizontalGridlines);

    // Color scale
    var color = d3.scaleOrdinal(d3.schemeCategory10);
    
    // uncomment to place legend vertically
    // let legendBuffer = this.dimensions.width/this.dataset.length; // spacing for the legend

    // horizontally spaced legend
    let legendBuffer = this.dimensions.height/this.dataset.length; // spacing for the legend

    let appendPath = (d, i) => {
      let key = d.key
      let lineColor = "gray"
      if (key in this.legendColors){
        lineColor = this.legendColors[key];
      }
      else if(this.dataset.length>1){
        lineColor = color(i);
      }
      this.svg_graph_ctr.append("path")
        .attr("class", "line")
        .style("stroke", lineColor)
        .attr("d", this.valueline(d.value))
          
      this.svg_graph.append("text")
        .attr("x", this.dimensions.ctrWidth+115)
        .attr("y", (legendBuffer/2)+i*legendBuffer)

        .attr("class", "legend")    // style the legend
        .style("fill", lineColor).style("word-wrap", "break-word")
        .text(this.validLegendEntries[d.key]);
    }
    this.dataset.forEach(appendPath)

  }

}